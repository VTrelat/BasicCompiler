import sys
import lark

COUNT = iter(range(10000))

# grammar
grammar = lark.Lark("""
variables : ID ("," ID)*
expr : ID -> variable
     | NUMBER -> number
     | expr OP expr -> binexpr
     | "(" expr ")" -> parenexpr
cmd : ID "=" expr ";" -> assignment
    | "while" "(" expr ")" "{" bloc "}" -> while
    | "if" "(" expr ")" "{" bloc "}" -> if
    | "if" "(" expr ")" "{" bloc "}" "else" "{" bloc "}" -> ifelse
    | cmd ";" cmd
    | "printf" "(" expr ")" ";" -> printf
bloc : (cmd)*
program : "main" "(" variables ")" "{" bloc "return" expr ";" "}" -> main
NUMBER : /\d+/
OP : "+" | "-" | "*" | "/" | "^" | "==" | "!=" | "<" | ">"
ID : /[a-zA-Z][a-zA-Z0-9]*/
%import common.WS
%ignore WS
""", start="program")


# prettify parsed program
def prettify_variables(variables):
    return ", ".join([var.value for var in variables.children])


def prettify_expr(expr):
    if expr.data in ["variable", "number"]:
        return expr.children[0].value
    elif expr.data == "binexpr":
        return f"{prettify_expr(expr.children[0])} {expr.children[1].value} {prettify_expr(expr.children[2])}"
    elif expr.data == "parenexpr":
        return f"({prettify_expr(expr.children[1])})"
    else:
        raise Exception("Unknown expr")


def prettify_cmd(cmd, indent):
    if cmd.data == "assignment":
        return f"{cmd.children[0].value} = {prettify_expr(cmd.children[1])};"
    elif cmd.data in ["while", "if"]:
        return f"{cmd.data} ({prettify_expr(cmd.children[0])}) {{\n{prettify_bloc(cmd.children[1], indent)}\n{indent}}}"
    elif cmd.data == "ifelse":
        return f"if ({prettify_expr(cmd.children[0])}) {{\n{prettify_bloc(cmd.children[1], indent)}\n{indent}}}\n{indent}else {{\n{prettify_bloc(cmd.children[2], indent)}\n{indent}}}"
    elif cmd.data == "printf":
        return f"printf({prettify_expr(cmd.children[0])});"
    else:
        raise Exception("Unknown cmd")


def prettify_bloc(bloc, indent=""):
    indent += "    "
    return indent+f"\n{indent}".join([prettify_cmd(cmd, indent) for cmd in bloc.children])


def prettify(program):
    vars = prettify_variables(program.children[0])
    bloc = prettify_bloc(program.children[1], "")
    ret = prettify_expr(program.children[2])
    return f"main({vars}) {{\n{bloc}\n    return {ret};\n}}"


# Build assembler code
def var_list(ast):
    if isinstance(ast, lark.Token):
        if ast.type == "ID":
            return {ast.value}
        else:
            return set()
    s = set()
    for c in ast.children:
        s.update(var_list(c))
    return s


def compile_expr(expr):
    if expr.data == "variable":
        return f"   mov rax, [{expr.children[0].value}]"
    if expr.data == "number":
        return f"   mov rax, {expr.children[0].value}"
    elif expr.data == "binexpr":
        e1 = compile_expr(expr.children[0])
        e2 = compile_expr(expr.children[2])
        op = expr.children[1].value
        opstr = "add"
        if op == "-":
            opstr = "sub"
        elif op == "*":
            opstr = "imul"
        elif op == "/":
            opstr = "idiv"
        return f"{e2}\n   push rax\n{e1}\n   pop rbx\n   {opstr} rax rbx\n"
    elif expr.data == "parenexpr":
        return compile_expr(expr.children[0])
    else:
        raise Exception("Not implemented")


def compile_cmd(cmd):
    if cmd.data == "assignment":
        lhs = cmd.children[0].value
        rhs = compile_expr(cmd.children[1])
        return f"{rhs}\n   mov [{lhs}], rax"
    elif cmd.data == "printf":
        return f"{compile_expr(cmd.children[0])}\n   call _printf"
    elif cmd.data in {"while", "if"}:
        e = compile_expr(cmd.children[0])
        b = compile_bloc(cmd.children[1])
        index = next(COUNT)
        return f"{cmd.data}_{index}:\n{e}\ncmp rax, 0\n   jz end{cmd.data}_{index}\n{b}\n   jmp {cmd.data}_{index}\nend{cmd.data}_{index}:\n"
    elif cmd.data == "ifelse":
        e = compile_expr(cmd.children[0])
        b1 = compile_bloc(cmd.children[1])
        b2 = compile_bloc(cmd.children[2])
        index = next(COUNT)
        return f"{cmd.data}_{index}:\n{e}\n   cmp rax, 0\n   jz end{cmd.data}_{index}\n{b1}\njmp endif{cmd.data}_{index}\n{b2}\nendif{cmd.data}_{index}:\n"
    else:
        raise Exception("Not implemented")


def compile_bloc(bloc):
    return "\n".join([compile_cmd(t) for t in bloc.children])


def compile(program: str) -> str:
    with open("template.asm") as f:
        template = f.read()
        var_decl = "\n".join([f"{x} : dq 0" for x in var_list(program)])
        template = template.replace("VAR_DECL", var_decl)
        template = template.replace(
            "RETURN", compile_expr(program.children[2]))
        template = template.replace("BODY", compile_bloc(program.children[1]))
        f.close()
        return template


with open("program.opale", "r") as f:
    program = grammar.parse(str(f.read()))
    print(compile(program))

# def save_to_file(filename: str, content: str) -> None:
#     with open(filename, "w") as f:
#         f.write(content)


# if len(sys.argv) > 1:
#     with open(sys.argv[1], "r") as f:
#         print("Parsing...")
#         program = grammar.parse(str(f.read()))
#         save_to_file(sys.argv[1], prettify(program))
#     print("Saving to file...")
#     save_to_file(sys.argv[2], build_assembler(program))
#     print(f"Saved to {sys.argv[2]}")
# else:
#     print("Give two arguments: program and filename")
