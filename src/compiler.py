import lark

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
program : "main" "(" variables ")" "{" bloc "return" "(" expr ")" ";" "}" -> main
NUMBER : /\d+/
OP : "+" | "-" | "*" | "/" | "^" | "==" | "!=" | "<" | ">" | "<=" | ">="
ID : /[a-zA-Z][a-zA-Z0-9]*/
%import common.WS
%ignore WS
""", start="program")

# print(grammar.parse(
#     "main(x,y,z) { printf(x); printf(y); printf(z); return(x+y+z); }"))


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
    return f"main({vars}) {{\n{bloc}\n    return ({ret});\n}}"


# Build assembler code
def body_asm(body):
    asm = ""
    for cmd in body.children:
        if cmd.data == "assignment":

        elif cmd.data == "printf":

        elif cmd.data == "while":

        elif cmd.data == "if":


def build_assembler(program):
    vars = prettify_variables(program.children[0])
    body = prettify_bloc(program.children[1])
    ret = prettify_expr(program.children[2])

    return f"section .data \n{vars} \nsection .text \nmain: \n{body} \nreturn: \n    mov eax, {ret} \n    ret"


program = grammar.parse(
    """
main(x,y) {
x = 1;
y = 2;
return(x+y);
}
""")

print(prettify(program))

print(build_assembler(program))
