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
def expr_asm(expr):
    asm = ""
    if expr.data == "variable":
        return f"    mov rax, [{expr.children[0].value}] \n"
    
    if expr.data == "number":
        return f"    mov rax, {expr.children[0].value} \n"
    
    elif expr.data == "binexpr":
        if expr.children[1].value == "+":
            asm += expr_asm(expr.children[2])
            asm += "    push rax\n"
            asm += expr_asm(expr.children[0])
            asm += "    add rax, rbx\n"
        else :
            raise Exception("Unknown operator")
        return f"    {expr.children[1].value} rax, rbx"
    
    elif expr.data == "parenexpr":
        expr_asm(expr.children[1])
        return ""
    
    else:
        raise Exception("Unknown expr")

def cmd_asm(body):
    asm = ""
    for cmd in body.children:
        if cmd.data == "assignment":
            asm += expr_asm(cmd.children[1])
            asm += f"    mov [{cmd.children[0].value}], rax\n"
        elif cmd.data == "printf":
            expr_asm(cmd.children[0])
            asm += f"    call _printf\n"
        elif cmd.data == "while":
            asm += f"    while_{cmd.children[0].value}: \n"
            asm += expr_asm(cmd.children[1])
            asm += f"    cmp rax, 0\n"
            asm += f"    je endwhile_{cmd.children[0].value}\n"
            asm += cmd_asm(cmd.children[2])
            asm += f"    jmp while_{cmd.children[0].value}\n"
            asm += f"endwhile_{cmd.children[0].value}: \n"
        elif cmd.data == "if":
            asm += f"    if_{cmd.children[0].value}: \n"
            asm += expr_asm(cmd.children[1])
            asm += f"    cmp rax, 0\n"
            asm += f"    je endif_{cmd.children[0].value}\n"
            asm += cmd_asm(cmd.children[2])
            asm += f"    jmp endif_{cmd.children[0].value}\n"
            asm += f"endif_{cmd.children[0].value}: \n"
    return asm

def var_asm(variables):
    return "\n".join([f"    {var.value}: dq 0" for var in variables.children])

def build_assembler(program):
    vars = var_asm(program.children[0])
    body = cmd_asm(program.children[1])
    ret = expr_asm(program.children[2])

    return f"section .data \n{vars} \nsection .text \nmain: \n{body} \nreturn: \n{ret}    ret"


program = grammar.parse(
    """
main(x, y) {
x = 1;
y = 2;
return(x + y);
}
""")
# print("Parsed program:")
# print(prettify(program)+"\n")


print("Assembler code:")
print(build_assembler(program))
