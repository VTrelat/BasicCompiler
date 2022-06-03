from collections import namedtuple
import lark


# storage of function types and names
Var = namedtuple("Var", ["type", "id"])


def count_char(string, char):
    return sum(1 for c in string if c == char)


def fun_list(prog: lark.Tree) -> set[Var]:
    return {
        # c.children[0].value == c.children[0]
        Var(c.children[0], c.children[1])
        for c in prog.children
    }


def var_list(function: lark.Tree) -> set[Var]:
    if isinstance(function, lark.Token):
        if function.type == "ID":
            return {function.value}
        else:
            return set()
    s = set()
    for c in function.children:
        s.update(var_list(c))
    return s
