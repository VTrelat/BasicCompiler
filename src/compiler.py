#! /usr/bin/env python3
import sys
import lark
import platform
from utils import fun_list, var_list, count_char, var_offsets

sys_name = platform.system()
if sys_name == "Linux":
    F_LEADER = ""
    TEMPLATE = "linux_template.asm"
elif sys_name == "Darwin":
    F_LEADER = "_"
    TEMPLATE = "darwin_template.asm"
else:
    raise Exception("Platform not supported")

COUNT = iter(range(10000))
op2asm = {"+": "add", "-": "sub", "*": "mul", "/": "div"}
types = {
    "int": 8,
    "char": 1,
    "int *": 8
}
functions = None

# grammar
grammar = lark.Lark("""
%import common.NEWLINE
variables : TYPE ID ("," TYPE ID)*
expr : ID -> variable
     | NUMBER -> number
     | expr OP expr -> binexpr
     | "(" expr ")" -> parenexpr
     | ID "(" expr ("," expr)* ")" -> fcall
cmd : TYPE ID "=" expr ";" -> initialization
    | TYPE ID ";" -> declaration
    | ID "=" expr ";" -> assignment
    | "while" "(" expr ")" "{" bloc "}" -> while
    | "if" "(" expr ")" "{" bloc "}" -> if
    | "if" "(" expr ")" "{" bloc "}" "else" "{" bloc "}" -> ifelse
    | cmd ";" cmd
    | "printf" "(" expr ")" ";" -> printf
    | COMMENT
    | "giveMeBack" expr ";" -> return
bloc : (cmd)*
function : TYPE ID "(" variables ")" "{" bloc "}"
TYPE : /(int|char)\s*[*\s*]*/
COMMENT : "(*" /(.|\\n|\\r)+/ "*)" |  "//" /(.)+/ NEWLINE
program : function+
NUMBER : /\d+/
OP : "+" | "-" | "*" | "/" | "^" | "==" | "!=" | "<" | ">"
ID : /[a-zA-Z][a-zA-Z0-9]*/
%ignore COMMENT
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
    return f"{function.children[0].value.strip()} {function.children[1].value}({vars}) {{\n{bloc}\n}}"


def prettify_expr(expr: lark.Tree) -> str:
    if expr.data in ["variable", "number"]:
        return expr.children[0].value
    elif expr.data == "binexpr":
        return f"{prettify_expr(expr.children[0])} {expr.children[1].value} {prettify_expr(expr.children[2])}"
    elif expr.data == "parenexpr":
        return f"({prettify_expr(expr.children[1])})"
    elif expr.data == "fcall":
        args = ','.join([prettify_expr(e) for e in expr.children[1:]])
        return f"{expr.children[0].value}({args})"
    else:
        raise Exception("Unknown expr", expr.data)


def prettify_cmd(cmd: lark.Tree, indent: str) -> str:
    if cmd.data == "initialization":
        n = count_char(cmd.children[0], "*")
        t = cmd.children[0].value.replace('*', '').strip()
        t = t.split(" ")[0] + (1 if n != 0 else 0)*" " + n*'*'
        return f"{t} {cmd.children[1].value} = {prettify_expr(cmd.children[2])};"
    elif cmd.data == "declaration":
        n = count_char(cmd.children[0], "*")
        t = cmd.children[0].value.replace('*', '').strip()
        t = t.split(" ")[0] + (1 if n != 0 else 0)*" " + n*'*'
        return f"{t} {cmd.children[1].value};"
    elif cmd.data == "assignment":
        return f"{cmd.children[0].value} = {prettify_expr(cmd.children[1])};"
    elif cmd.data in ["while", "if"]:
        return f"{cmd.data} ({prettify_expr(cmd.children[0])}) {{\n{prettify_bloc(cmd.children[1], indent)}\n{indent}}}"
    elif cmd.data == "ifelse":
        return f"if ({prettify_expr(cmd.children[0])}) {{\n{prettify_bloc(cmd.children[1], indent)}\n{indent}}}\n{indent}else {{\n{prettify_bloc(cmd.children[2], indent)}\n{indent}}}"
    elif cmd.data == "printf":
        return f"printf({prettify_expr(cmd.children[0])});"
    elif cmd.data == "COMMENT":
        return ""
    elif cmd.data == "return":
        return f"giveMeBack {prettify_expr(cmd.children[0])};"
    else:
        raise Exception("Unknown cmd", cmd.data)


def prettify_bloc(bloc: lark.Tree, indent: str = "") -> str:
    indent += "    "
    return indent+f"\n{indent}".join([prettify_cmd(cmd, indent) for cmd in bloc.children])


def prettify(program: lark.ParseTree) -> str:
    return "\n".join([prettify_function(f) for f in program.children])


# Build assembler code
def compile_expr(expr: lark.Tree, offsets: dict[str, int] = None) -> str:
    if expr.data == "variable":
        return f"   mov rax, [rbp{offsets[expr.children[0].value]:+}]"
    if expr.data == "number":
        return f"   mov rax, {expr.children[0].value}"
    elif expr.data == "binexpr":
        e1 = compile_expr(expr.children[0], offsets)
        e2 = compile_expr(expr.children[2], offsets)
        op = expr.children[1].value
        return f"{e2}\n   push rax\n{e1}\n   pop rbx\n   {op2asm[op]} rax, rbx\n"
    elif expr.data == "parenexpr":
        return compile_expr(expr.children[0], offsets)
    elif expr.data == "function":
        bloc = compile_bloc(expr.children[3], offsets)
        out = F_LEADER+expr.children[1].value.strip()
        print(offsets, offsets.values())
        # size of the variables defined in the funciton, and not the arguments
        noffsets = list(filter(lambda x: x < 0, offsets.values()))
        varSize = -min(noffsets) if len(noffsets) > 0 else 0
        return (f"{out}:\n   push rbp\n   mov rbp, rsp\n   sub rsp, {varSize}\n"
                f"   push rdi\n   push rsi\n"
                f"   {bloc}\n\n")
                # f"   pop rdi\n   pop rsi\n   add rsp, {varSize}\n   pop rbp\n   ret\n\n")
    elif expr.data == "fcall":
        fid = F_LEADER+expr.children[0].value
        args = '\n'.join(compile_expr(e, offsets) +
                         '\n   push rax' for e in expr.children[1:])
        callee_offests = var_offsets(
            var_list(functions[expr.children[0].value].tree), types)
        argsSize = max(callee_offests.values()) - 8
        return f"{args}\n   call {fid}\n   add rsp, {argsSize}\n"
    else:
        raise Exception("Not implemented : "+expr.data)


def compile_cmd(cmd: lark.Tree, offsets: dict[str, int] = None) -> str:
    if cmd.data == "initialization":
        # now in cmd.children[0] is the type
        lhs = cmd.children[1].value
        rhs = compile_expr(cmd.children[2], offsets)
        return f"{rhs}\n   mov [rbp{offsets[lhs]:+}], rax"
    elif cmd.data == "declaration":
        return ""
    elif cmd.data == "assignment":
        lhs = cmd.children[0].value
        rhs = compile_expr(cmd.children[1], offsets)
        return f"{rhs}\n   mov [rbp{offsets[lhs]:+}], rax"
    elif cmd.data == "printf":
        return f"{compile_expr(cmd.children[0], offsets)}\n   mov rdi, fmt\n   mov rsi, rax\n   xor rax, rax\n   call {F_LEADER}printf"
    elif cmd.data == "while":
        e = compile_expr(cmd.children[0], offsets)
        b = compile_bloc(cmd.children[1], offsets)
        index = next(COUNT)
        return f"{cmd.data}{index} :\n{e}\n   cmp rax, 0\n   jz end{cmd.data}{index}\n{b}\n   jmp {cmd.data}{index}\nend{cmd.data}{index} :\n"
    elif cmd.data == "if":
        e = compile_expr(cmd.children[0], offsets)
        b = compile_bloc(cmd.children[1], offsets)
        return f"{cmd.data} :\n{e}\n   cmp rax, 0\n   jz end{cmd.data}\n{b}\nend{cmd.data} :\n"
    elif cmd.data == "ifelse":
        e = compile_expr(cmd.children[0], offsets)
        b1 = compile_bloc(cmd.children[1], offsets)
        b2 = compile_bloc(cmd.children[2], offsets)
        index = next(COUNT)
        return f"{cmd.data}{index} :\n{e}\n   cmp rax, 0\n   jz end{cmd.data}{index}\n{b1}\njmp end{cmd.data}{index}\n{b2}\nend{cmd.data}{index} :\n"
    elif cmd.data == "COMMENT":
        return ""
    elif cmd.data == "return":
        noffsets = list(filter(lambda x: x < 0, offsets.values()))
        varSize = -min(noffsets) if len(noffsets) > 0 else 0
        return (f"   pop rdi\n   pop rsi\n   add rsp, {varSize}\n"
                f"   {compile_expr(cmd.children[0], offsets)}\n"
                f"   pop rbp\n   ret\n")
    else:
        raise Exception("Not implemented", cmd.data)


def compile_bloc(bloc: lark.Tree, offsets: dict[str, int] = None) -> str:
    return "\n".join([compile_cmd(t, offsets) for t in bloc.children])


def compile_var(ast: lark.Tree) -> str:
    s = ""
    for i in range(len(ast.children)):
        s += f"   mov rbx, [rbp-0x10]\n   mov rdi, [rbx+{8*(i+1)}]\n   call _atoi\n   mov [{ast.children[i].value}], rax\n"
    return s


def compile(program: lark.ParseTree) -> str:
    global functions
    functions = fun_list(program)
    with open(TEMPLATE) as f:
        template = f.read()
        var_decl = "\n".join([f"{x} : dq 0" for x in var_list(program)])
        template = template.replace("VAR_DECL", var_decl)

        func_asm = ""
        for function in program.children:
            # child.data : function symbol
            # child.children[0].value : function type
            # child.children[1].value : function name
            vars = var_list(function)
            print(vars)
            offsets = var_offsets(vars, types)
            print(offsets)
            func_asm += compile_expr(function, offsets)
        template = template.replace("FUN_DECL", func_asm)
        # template = template.replace(
        #     "RETURN", compile_expr(program.children[2]))
        # template = template.replace("BODY", compile_bloc(program.children[1]))
        # template = template.replace(
        #     "VAR_INIT", compile_var(program.children[0]))
        f.close()
        return template


# with open("program.opale", "r") as f:
#     program = grammar.parse(str(f.read()))
#     print(compile(program))

def save_to_file(filename: str, content: str) -> None:
    with open(filename, "w") as f:
        f.write(content)


if len(sys.argv) > 1:
    with open(sys.argv[1], "r") as f:
        print("Parsing...")
        program = grammar.parse(str(f.read()))
        save_to_file(sys.argv[1], prettify(program))
    print("Saving to file...")
    print(compile(program))
    save_to_file(sys.argv[2], compile(program))
    print(f"Saved to {sys.argv[2]}")
else:
    print("Give two arguments: program and filename")
