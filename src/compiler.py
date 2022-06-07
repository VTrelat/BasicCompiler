#! /usr/bin/env python3
import getopt
import sys
import lark
import platform
import re
from dataclasses import dataclass
from utils import fun_list, var_list, count_char, var_offsets, Var, Fun

sys_name = platform.system()
if sys_name == "Linux":
    F_LEADER = ""
    from templates import LINUX_TEMPLATE as TEMPLATE
elif sys_name == "Darwin":
    F_LEADER = "_"
    from templates import DARWIN_TEMPLATE as TEMPLATE
else:
    raise Exception("Platform not supported")


@dataclass
class Env:
    count = iter(range(10000))
    funID: str
    varLists: dict[str, Var]
    functionList: dict[str, Fun]
    offsets: dict[str, dict[str, int]]
    pdepth: int = 0
    curVar: str = ""


ASM_BINOP = {"+": "add", "-": "sub", "*": "imul", "/": "idiv"}
ASM_COMPARATOR = {
    "==": "sete",
    "!=": "setne",
    "<=": "setle",
    ">=": "setge",
    "<": "setl",
    ">": "setg"
}
ASM_MONOP = {"&": "lea", "-": "neg"}
TYPES = {
    "int": 8,
    "char": 1
}
ASM_POINTER_SIZE = {
    1: "byte",
    2: "word",
    4: "dword",
    8: "qword"
}
AX_REGISTERS = {
    1: "al",
    2: "ax",
    4: "eax",
    8: "rax"
}

# grammar
grammar = lark.Lark("""
%import common.NEWLINE
variables : (TYPE ID)? ("," TYPE ID)*
expr : ID -> variable
     | NUMBER -> number
     | expr OP expr -> binexpr
     | expr COMPARATOR expr -> comparison
     | "(" expr ")" -> parenexpr
     | P_OP ID -> pexpr
     | MONOP expr -> monexpr
     | deref -> deref
     | ID "(" expr? ("," expr)* ")" -> fcall
deref : "*" deref -> follow_pointer
      | ID -> variable
cmd : TYPE ID "=" expr ";" -> initialization
    | TYPE ID ";" -> declaration
    | ID "=" expr ";" -> assignment
    | "*" deref "=" expr ";" -> passignment
    | "while" "(" expr ")" "{" bloc "}" -> while
    | "if" "(" expr ")" "{" bloc "}" -> if
    | "if" "(" expr ")" "{" bloc "}" "else" "{" bloc "}" -> ifelse
    | cmd ";" cmd
    | "printf" "(" expr ")" ";" -> printf
    | COMMENT -> comment
    | "giveMeBack" expr ";" -> return
    | "getMeVar" ID ";" -> readint
bloc : (cmd)*
function : TYPE ID "(" variables ")" "{" bloc "}"
TYPE : /(int|char)\s*[*\s*]*/
COMMENT : "(*" /(.|\\n|\\r)+/ "*)" |  "//" /(.)+/ NEWLINE
program : function+
NUMBER : /[-+]?\d+/
OP : "+" | "-" | "*" | "/"
MONOP : "-"
COMPARATOR : "==" | "<=" | ">=" | "<" | ">" | "!="
P_OP : "&"
ID : /[a-zA-Z][a-zA-Z0-9]*/
%import common.WS
%ignore WS
""", start="program")


# prettify parsed program
def prettify_variables(variables: lark.Tree) -> str:
    out = ""
    for i in range(len(variables.children)):
        if i % 2 == 0:
            out += f"{variables.children[i].value.strip()} "
        else:
            out += f"{variables.children[i].value}, "
    return out[:-2]


def prettify_function(function: lark.Tree) -> str:
    vars = prettify_variables(function.children[2])
    bloc = prettify_bloc(function.children[3], "")
    type = function.children[0].value.strip()
    function_id = function.children[1].value
    return f"{type} {function_id}({vars}) {{\n{bloc}\n}}"


def prettify_expr(expr: lark.Tree) -> str:
    if expr.data in ["variable", "number"]:
        return expr.children[0].value
    elif expr.data == "binexpr":
        lhs = prettify_expr(expr.children[0])
        op = expr.children[1].value
        rhs = prettify_expr(expr.children[2])
        return f"{lhs} {op} {rhs}"
    elif expr.data == "pexpr":
        return f"{expr.children[0].value}{expr.children[1].value}"
    elif expr.data == "parenexpr":
        return f"({prettify_expr(expr.children[1])})"
    elif expr.data == "follow_pointer":
        return f"*{prettify_expr(expr.children[0])}"
    elif expr.data == "deref":
        return prettify_expr(expr.children[0])
    elif expr.data == "fcall":
        args = ','.join([prettify_expr(e) for e in expr.children[1:]])
        return f"{expr.children[0].value}({args})"
    elif expr.data == "monexpr":
        return f"{expr.children[0].value}{prettify_expr(expr.children[1])}"
    elif expr.data == "comparison":
        lhs = prettify_expr(expr.children[0])
        comparator = expr.children[1].value
        rhs = prettify_expr(expr.children[2])
        return f"{lhs} {comparator} {rhs}"
    else:
        raise Exception("Unknown expr", expr.data)


def prettify_cmd(cmd: lark.Tree, indent: str) -> str:
    if cmd.data == "initialization":
        n = count_char(cmd.children[0], "*")
        t = cmd.children[0].value.replace('*', '').strip()
        t = t.split(" ")[0] + (1 if n != 0 else 0)*" " + n*'*'
        expr = prettify_expr(cmd.children[2])
        return f"{t} {cmd.children[1].value} = {expr};"
    elif cmd.data == "declaration":
        n = count_char(cmd.children[0], "*")
        t = cmd.children[0].value.replace('*', '').strip()
        t = t.split(" ")[0] + (1 if n != 0 else 0)*" " + n*'*'
        return f"{t} {cmd.children[1].value};"
    elif cmd.data == "assignment":
        return f"{cmd.children[0].value} = {prettify_expr(cmd.children[1])};"
    elif cmd.data == "passignment":
        deref = prettify_expr(cmd.children[0])
        return (f"*{deref} = {prettify_expr(cmd.children[1])};")
    elif cmd.data in ["while", "if"]:
        return (f"{cmd.data} ({prettify_expr(cmd.children[0])}) {{\n"
                f"{prettify_bloc(cmd.children[1], indent)}\n"
                f"{indent}}}")
    elif cmd.data == "ifelse":
        return (f"if ({prettify_expr(cmd.children[0])}) {{\n"
                f"{prettify_bloc(cmd.children[1], indent)}\n"
                f"{indent}}}\n"
                f"{indent}else {{\n"
                f"{prettify_bloc(cmd.children[2], indent)}\n"
                f"{indent}}}")
    elif cmd.data == "printf":
        return f"printf({prettify_expr(cmd.children[0])});"
    elif cmd.data == "comment":
        return cmd.children[0].value.strip()
    elif cmd.data == "return":
        return f"giveMeBack {prettify_expr(cmd.children[0])};"
    elif cmd.data == "readint":
        return f"getMeVar {cmd.children[0].value};"
    else:
        raise Exception("Unknown cmd", cmd.data)


def prettify_bloc(bloc: lark.Tree, indent: str = "") -> str:
    indent += "    "
    return indent+f"\n{indent}".join([prettify_cmd(cmd, indent) for cmd in bloc.children])


def prettify(program: lark.ParseTree) -> str:
    return "\n".join([prettify_function(f) for f in program.children])


# Build assembler code
def compile_expr(expr: lark.Tree, env: dict[str, int] = None, varDict: dict[str, int] = None) -> str:
    funID = env.funID
    offsets = env.offsets[funID]
    varList = env.varLists[funID]
    if expr.data == "variable":
        varID = expr.children[0].value
        if varList[varID].pdepth > env.pdepth:
            # pointer
            cmd = "mov"
            size = 8
        elif TYPES[varList[varID].type] == 8:
            # type of size 64bit
            cmd = "mov"
            size = 8
        else:
            cmd = "movsx"
            size = TYPES[varList[varID].type]
        env.curVar = varID
        return f"   {cmd} rax, {ASM_POINTER_SIZE[size]} [rbp{offsets[varID]:+}]"
    elif expr.data == "number":
        return f"   mov rax, {expr.children[0].value}"
    elif expr.data == "binexpr":
        e1 = compile_expr(expr.children[0], env)
        e2 = compile_expr(expr.children[2], env)
        op = ASM_BINOP[expr.children[1].value]
        return f"{e2}\n   push rax\n{e1}\n   pop rbx\n   {op} rax, rbx\n"
    elif expr.data == "monexpr":
        e1 = compile_expr(expr.children[1], env)
        op = ASM_MONOP[expr.children[0].value]
        return f"{e1}\n   {op} rax\n"
    elif expr.data == "comparison":
        e1 = compile_expr(expr.children[0], env)
        e2 = compile_expr(expr.children[2], env)
        op = ASM_COMPARATOR[expr.children[1].value]
        return (f"{e2}\n"
                f"   push rax\n"
                f"{e1}\n"
                f"   pop rbx\n"
                f"   cmp rax, rbx\n"
                f"   {op} al\n"
                f"   and rax, 0x000000ff")
    elif expr.data == "pexpr":
        op = expr.children[0].value
        return f"   {ASM_MONOP[op]} rax, [rbp{offsets[expr.children[1].value]:+}]\n"
    elif expr.data == "follow_pointer":
        prev = compile_expr(expr.children[0], env)
        env.pdepth += 1
        size = 8 if env.pdepth == varList[env.curVar].pdepth else TYPES[varList[env.curVar].type]
        return f"{prev}\n   mov rax, [rax]\n"
    elif expr.data == "deref":
        env.pdepth = 0
        env.curVar = ""
        res = compile_expr(expr.children[0], env)
        env.curVar = ""
        env.pdepth = 0
        return res
    elif expr.data == "parenexpr":
        return compile_expr(expr.children[0], env)
    elif expr.data == "function":
        bloc = re.sub("\n[\n]+", '\n',
                      compile_bloc(expr.children[3], env))
        # print(bloc)
        out = F_LEADER+expr.children[1].value.strip()
        # print(offsets, offsets.values())
        # size of the variables defined in the funciton, and not the arguments
        noffsets = list(filter(lambda x: x < 0, offsets.values()))
        varSize = -min(noffsets) if len(noffsets) > 0 else 0
        varSize = varSize if varSize % 16 == 0 else (varSize // 16 + 1) * 16
        return (f"{out}:\n"
                f"   push rbp\n"
                f"   mov rbp, rsp\n"
                f"   sub rsp, {varSize}\n"
                f"   push rdi\n"
                f"   push rsi\n"
                f"   {bloc}\n\n")
    elif expr.data == "fcall":
        calleeID = F_LEADER+expr.children[0].value
        args = '\n'.join(compile_expr(e, env) +
                         '\n   push rax' for e in expr.children[1:])
        callee_offests = env.offsets[expr.children[0].value]
        argsSize = max(callee_offests.values()) - 8 if len(callee_offests.values()) > 0 else 0
        return (f"{args}\n"
                f"   call {calleeID}\n"
                f"   add rsp, {argsSize}\n")
    else:
        raise Exception("Not implemented : "+expr.data)


def compile_cmd(cmd: lark.Tree, env: Env) -> str:
    funID = env.funID
    offsets = env.offsets[funID]
    if cmd.data == "initialization":
        # now in cmd.children[0] is the type
        lhs = cmd.children[1].value
        rhs = compile_expr(cmd.children[2], env)
        v = env.varLists[funID][lhs]
        tsize = TYPES[v.type]
        cmd = "mov" if TYPES[v.type] > 2 else "movsx"
        return (f"{rhs}\n"
                f"   mov {ASM_POINTER_SIZE[tsize]} [rbp{offsets[lhs]:+}], {AX_REGISTERS[tsize]}")
    elif cmd.data == "declaration":
        return ""
    elif cmd.data == "assignment":
        lhs = cmd.children[0].value
        rhs = compile_expr(cmd.children[1], env)
        v = env.varLists[funID][lhs]
        # print("env", env)
        tsize = TYPES[v.type] if v.pdepth == env.pdepth else 8
        return (f"{rhs}\n"
                f"   mov {ASM_POINTER_SIZE[tsize]} [rbp{offsets[lhs]:+}], {AX_REGISTERS[tsize]}")
    elif cmd.data == "passignment":
        return (f"{compile_expr(cmd.children[0], env)}\n"
                f"   push rax\n"
                f"{compile_expr(cmd.children[1], env)}\n"
                f"   mov rbx, rax\n"
                f"   pop rax\n"
                f"   mov [rax], rbx")
    elif cmd.data == "printf":
        return (f"{compile_expr(cmd.children[0], env)}\n"
                f"   mov rdi, fmt\n"
                f"   mov rsi, rax\n"
                f"   xor rax, rax\n"
                f"   call {F_LEADER}printf")
    elif cmd.data == "while":
        e = compile_expr(cmd.children[0], env)
        b = compile_bloc(cmd.children[1], env)
        index = next(env.count)
        return (f"{cmd.data}{index} :\n"
                f"{e}\n"
                f"   cmp rax, 0\n"
                f"   jz end{cmd.data}{index}\n"
                f"{b}\n"
                f"   jmp {cmd.data}{index}\n"
                f"end{cmd.data}{index} :\n")
    elif cmd.data == "if":
        e = compile_expr(cmd.children[0], env)
        b = compile_bloc(cmd.children[1], env)
        return (f"{cmd.data} :\n"
                f"{e}\n"
                f"   cmp rax, 0\n"
                f"   jz end{cmd.data}\n"
                f"{b}\n"
                f"end{cmd.data} :\n")
    elif cmd.data == "ifelse":
        e = compile_expr(cmd.children[0], env)
        b1 = compile_bloc(cmd.children[1], env)
        b2 = compile_bloc(cmd.children[2], env)
        index = next(env.count)
        return (f"{cmd.data}{index} :\n{e}\n"
                f"   cmp rax, 0\n"
                f"   jz alt{cmd.data}{index}\n"
                f"{b1}\n"
                f"   jmp end{cmd.data}{index}\n"
                f"alt{cmd.data}{index} :\n"
                f"{b2}\n"
                f"end{cmd.data}{index} :\n")
    elif cmd.data == "comment":
        return ""
    elif cmd.data == "return":
        noffsets = list(filter(lambda x: x < 0, offsets.values()))
        varSize = -min(noffsets) if len(noffsets) > 0 else 0
        varSize = varSize if varSize % 16 == 0 else (varSize // 16 + 1) * 16
        retSize = TYPES[env.functionList[funID].type]
        cohersion = "   movsx rax {AX_REGISTERS[types[env.functionList[funID].type]]}\n" if retSize < 8 else ""
        return (f"   pop rdi\n"
                f"   pop rsi\n"
                f"   add rsp, {varSize}\n"
                f"{compile_expr(cmd.children[0], env)}\n"
                f"   {cohersion}"
                f"   pop rbp\n"
                f"   ret\n")
    elif cmd.data == "readint":
        lhs = cmd.children[0].value
        return (f"   lea rax, [rbp{offsets[lhs]:+}]\n"
                f"   mov rsi, rax\n"
                f"   mov rdi, read\n"
                f"   xor rax, rax\n"
                f"   call __isoc99_scanf\n")
    else:
        raise Exception("Not implemented", cmd.data)


def compile_bloc(bloc: lark.Tree, env: Env) -> str:
    return "\n".join([compile_cmd(t, env) for t in bloc.children])


def compile_var(ast: lark.Tree) -> str:
    s = ""
    for i in range(len(ast.children)):
        s += (f"   mov rbx, [rbp-0x10]\n"
              f"   mov rdi, [rbx+{8*(i+1)}]\n"
              f"   call _atoi\n"
              f"   mov [{ast.children[i].value}], rax\n")
    return s


def compile(program: lark.ParseTree) -> str:
    functions = fun_list(program)
    vars = {f.id: var_list(f.tree) for f in functions.values()}
    # print(vars)
    offsets = {f.id: var_offsets(vars[f.id].values(), TYPES)
               for f in functions.values()}
    env = Env(funID=None, functionList=functions,
              varLists=vars, offsets=offsets)
    template = TEMPLATE
    var_decl = "\n".join([f"{x} : dq 0" for x in var_list(program)])
    template = template.replace("VAR_DECL", var_decl)

    func_asm = ""
    for function in program.children:
        # child.data : function symbol
        # child.children[0].value : function type
        # child.children[1].value : function name
        # print(vars)
        # print(offsets)
        env.funID = function.children[1].value
        # print(env)
        func_asm += compile_expr(function, env)
    template = template.replace("FUN_DECL", func_asm)
    # template = template.replace(
    #     "RETURN", compile_expr(program.children[2]))
    # template = template.replace("BODY", compile_bloc(program.children[1]))
    # template = template.replace(
    #     "VAR_INIT", compile_var(program.children[0]))
    return template


# with open("program.opale", "r") as f:
#     program = grammar.parse(str(f.read()))
#     print(compile(program))
def save_to_file(filename: str, content: str) -> None:
    if filename == sys.stdout:
        print(content)
        return
    with open(filename, "w") as f:
        f.write(content)


def main(argv):
    outputFile = sys.stdout
    p = False
    try:
        opts, args = getopt.getopt(argv[1:], ':ho:p')
        inputFile = argv[0]
    except getopt.GetoptError:
        print("usage: compiler.py <inputFile> -o <outputFile>")
        sys.exit(1)
    except IndexError:
        print("You must provide an inputFile\n"
              "usage: compiler.py <inputFile> -o <outputFile>")
        sys.exit(1)
    except:
        print("usage: compiler.py <inputFile> -o <outputFile>")
        sys.exit(1)
    for opt, arg in opts:
        if opt == "-h":
            print("compile <inputFile> into asm and write to <outputFile> or stdin\n"
                  "usage: compiler.py <inputFile> -o <outputFile>\n"
                  "       -p    to prettify instead (write on inputFile)")
            sys.exit(0)
        elif opt == "-p":
            p = True
        elif opt == "-o":
            outputFile = arg
    with open(inputFile, 'r') as f:
        program = grammar.parse(str(f.read()))
        if p:
            save_to_file(inputFile, prettify(program))
        else:
            save_to_file(outputFile, compile(program))

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])




# if len(sys.argv) > 1:
#     with open(sys.argv[1], "r") as f:
#         print("Parsing...")
#         program = grammar.parse(str(f.read()))
#         save_to_file(sys.argv[1], prettify(program))
#     print("Saving to file...")
#     print(compile(program))
#     save_to_file(sys.argv[2], compile(program))
#     print(f"Saved to {sys.argv[2]}")
# else:
#     print("Give two arguments: program and filename")
