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
    if not isinstance(function, lark.Tree):
        return set()
    if function.data != "function":
        return set()
    # function.children[3] is the function bloc
    body = function.children[3]
    vars = function.children[2].children  # variables in function declaration
    res = {Var(t.value.strip(), i.value.strip())
           for t, i in zip(vars[::2], vars[1::2])}
    # adding the variables assigned in the bloc
    res.update({
        Var(c.children[0].value.strip(), c.children[1].value)
        for c in body.children
        if c.data == "initialization" or c.data == "declaration"
    })
    return res


def var_offsets(vars: set[Var], types: dict[str, int]) -> dict[str, int]:
    offset = 0
    res = {}
    for v in vars:
        offset += types[v.type]
        res[v.id] = offset
    return res
