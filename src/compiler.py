from turtle import pensize
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


def prettify_cmd(cmd):
    if cmd.data == "assignment":
        return f"{cmd.children[0].value} = {prettify_expr(cmd.children[1])};"
    elif cmd.data in ["while", "if"]:
        return f"{cmd.data} ({prettify_expr(cmd.children[0])}) {{\n{prettify_bloc(cmd.children[1])}\n}}"
    elif cmd.data == "printf":
        return f"printf({prettify_expr(cmd.children[0])});"
    else:
        raise Exception("Unknown cmd")


def prettify_bloc(bloc):
    return "\n".join([prettify_cmd(cmd) for cmd in bloc.children])


def prettify(program):
    vars = prettify_variables(program.children[0])
    bloc = prettify_bloc(program.children[1])
    ret = prettify_expr(program.children[2])
    return f"main ({vars}){{\n{bloc}\nreturn ({ret});\n}}"


# test with a while
program = grammar.parse(
    "main(x,y) { x = x + 1; while(x<y) { printf(x); x=x+1; } return(x+y); }")

program_parsed = grammar.parse(prettify(program))
print(program_parsed == program)
