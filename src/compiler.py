import sys
import lark

CIF: int = 0
CWHILE: int = 0

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
def expr_asm(expr, indent=""):
    asm = ""
    if expr.data == "variable":
        return f"{indent}mov rax, [{expr.children[0].value}] \n"

    if expr.data == "number":
        return f"{indent}mov rax, {expr.children[0].value} \n"

    elif expr.data == "binexpr":
        if expr.children[1].value == "+":
            asm += expr_asm(expr.children[2], indent)
            asm += f"{indent}push rax\n"
            asm += expr_asm(expr.children[0], indent)
            asm += f"{indent}add rax, rbx\n"
        elif expr.children[1].value == "-":
            asm += expr_asm(expr.children[2], indent)
            asm += f"{indent}push rax\n"
            asm += expr_asm(expr.children[0], indent)
            asm += f"{indent}sub rax, rbx\n"
        elif expr.children[1].value == "*":
            asm += expr_asm(expr.children[2], indent)
            asm += f"{indent}push rax\n"
            asm += expr_asm(expr.children[0], indent)
            asm += f"{indent}mul rax, rbx\n"
        elif expr.children[1].value == "/":
            asm += expr_asm(expr.children[2], indent)
            asm += f"{indent}push rax\n"
            asm += expr_asm(expr.children[0], indent)
            asm += f"{indent}div rax, rbx\n"
        elif expr.children[1].value == "^":
            asm += expr_asm(expr.children[2], indent)
            asm += f"{indent}push rax\n"
            asm += expr_asm(expr.children[0], indent)
            asm += f"{indent}pop rbx\n"
            asm += f"{indent}pop rax\n"
            asm += f"{indent}xor rax, rbx\n"
            asm += f"{indent}push rax\n"
        elif expr.children[1].value == "==":
            asm += expr_asm(expr.children[2], indent)
            asm += f"{indent}push rax\n"
            asm += expr_asm(expr.children[0], indent)
            asm += f"{indent}pop rbx\n"
            asm += f"{indent}pop rax\n"
            asm += f"{indent}cmp rax, rbx\n"
            asm += f"{indent}sete al\n"
            asm += f"{indent}movzb rax, al\n"
            asm += f"{indent}push rax\n"
        elif expr.children[1].value == "!=":
            asm += expr_asm(expr.children[2], indent)
            asm += f"{indent}push rax\n"
            asm += expr_asm(expr.children[0], indent)
            asm += f"{indent}pop rbx\n"
            asm += f"{indent}pop rax\n"
            asm += f"{indent}cmp rax, rbx\n"
            asm += f"{indent}setne al\n"
            asm += f"{indent}movzb rax, al\n"
            asm += f"{indent}push rax\n"
        elif expr.children[1].value == "<":
            asm += expr_asm(expr.children[2], indent)
            asm += f"{indent}push rax\n"
            asm += expr_asm(expr.children[0], indent)
            asm += f"{indent}pop rbx\n"
            asm += f"{indent}pop rax\n"
            asm += f"{indent}cmp rax, rbx\n"
            asm += f"{indent}setl al\n"
            asm += f"{indent}movzb rax, al\n"
            asm += f"{indent}push rax\n"
        elif expr.children[1].value == ">":
            asm += expr_asm(expr.children[2], indent)
            asm += f"{indent}push rax\n"
            asm += expr_asm(expr.children[0], indent)
            asm += f"{indent}pop rbx\n"
            asm += f"{indent}pop rax\n"
            asm += f"{indent}cmp rax, rbx\n"
            asm += f"{indent}setg al\n"
            asm += f"{indent}movzb rax, al\n"
            asm += f"{indent}push rax\n"
        else:
            raise Exception("Unknown operator")

    elif expr.data == "parenexpr":
        expr_asm(expr.children[1], indent)
        return ""

    else:
        raise Exception("Unknown expr")
    return asm


def cmd_asm(body, indent=""):
    global CIF, CWHILE
    asm = ""
    for cmd in body.children:
        if cmd.data == "assignment":
            asm += expr_asm(cmd.children[1], indent)
            asm += f"{indent}mov [{cmd.children[0].value}], rax\n"
        elif cmd.data == "printf":
            expr_asm(cmd.children[0], indent)
            asm += f"{indent}call _printf\n"
        elif cmd.data == "while":
            asm += f"while_{CWHILE}:\n"
            asm += expr_asm(cmd.children[0], indent)
            asm += f"{indent}cmp rax, 0\n"
            asm += f"{indent}je endwhile_{CWHILE}\n"
            asm += cmd_asm(cmd.children[1], indent)
            asm += f"{indent}jmp while_{CWHILE}\n"
            asm += f"endwhile_{CWHILE}\n"
            CWHILE += 1
        elif cmd.data == "if":
            asm += f"if_{CIF}:\n"
            asm += expr_asm(cmd.children[0], indent)
            asm += f"{indent}cmp rax, 0\n"
            asm += f"{indent}je endif_{CIF}\n"
            asm += cmd_asm(cmd.children[1], indent)
            asm += f"endif_{CIF}\n"
            CIF += 1
        elif cmd.data == "ifelse":
            asm += f"if_{CIF}:\n"
            asm += expr_asm(cmd.children[0], indent)
            asm += f"{indent}cmp rax, 0\n"
            asm += f"{indent}je endif_{CIF}\n"
            asm += cmd_asm(cmd.children[1], indent)
            asm += f"{indent}jmp endif_{CIF}\n"
            asm += cmd_asm(cmd.children[2], indent)
            asm += f"endif_{CIF}\n"
            CIF += 1
    return asm


def var_asm(variables, indent=""):
    return "\n".join([f"{indent}{var.value}: dq 0" for var in variables.children])


def build_assembler(program: str) -> str:
    vars = var_asm(program.children[0], indent="    ")
    body = cmd_asm(program.children[1], indent="    ")
    ret = expr_asm(program.children[2], indent="    ")

    return f"extern _printf\nglobal _main\nsection .data \n{vars} \nsection .text \n_main: \n{body} \nreturn: \n{ret}    ret"


def save_to_file(filename: str, content: str) -> None:
    with open(filename, "w") as f:
        f.write(content)


if len(sys.argv) > 1:
    with open(sys.argv[1], "r") as f:
        print("Parsing...")
        program = grammar.parse(str(f.read()))
        save_to_file(sys.argv[1], prettify(program))
    print("Saving to file...")
    save_to_file(sys.argv[2], build_assembler(program))
    print(f"Saved to {sys.argv[2]}")
else:
    print("Give two arguments: program and filename")
