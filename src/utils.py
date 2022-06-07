from collections import namedtuple
import lark

# storage of function types and names
Var = namedtuple("Var", ["type", "id", "argument",
                 "pdepth"], defaults=[False, 0])
Fun = namedtuple("Fun", ["type", "id", "tree"])


def count_char(string, char):
    return sum(1 for c in string if c == char)


def fun_list(prog: lark.Tree) -> dict[str, Fun]:
    return {
        # c.children[0].value == c.children[0]
        c.children[1].value.strip(): Fun(c.children[0].value.strip(),
                                         c.children[1].value.strip(),
                                         c)
        for c in prog.children
    }


def var_list(function: lark.Tree) -> dict[str, Var]:
    def get_name(var: str) -> str:
        return (var.strip().split(" "))[0]
    if not isinstance(function, lark.Tree):
        return {}
    if function.data != "function":
        return {}
    # function.children[3] is the function bloc
    body = function.children[3]
    vars = function.children[2].children  # variables in function declaration
    res = {i.value.strip():
           Var(get_name(t.value), i.value.strip(),
               True, count_char(t.value, "*"))
           for t, i in zip(vars[::2], vars[1::2])}
    # adding the variables assigned in the bloc
    res.update({
        c.children[1].value.strip():
        Var(get_name(c.children[0].value), c.children[1].value,
            False, count_char(c.children[0].value, "*"))
        for c in body.children
        if c.data == "initialization" or c.data == "declaration"
    })
    return res


def var_offsets(vars: list[Var], types: dict[str, int]) -> dict[str, int]:
    offset = 0
    noffset = 8 + len(list(filter(lambda v: v.argument, vars)))*8
    res = {}
    for v in vars:
        if v.argument:
            res[v.id] = noffset
            noffset -= 8
        else:
            if v.pdepth == 0:
                offset -= types[v.type]
                res[v.id] = offset
            else:
                offset -= 8
                res[v.id] = offset
    return res


def is_pointer(type: str) -> bool:
    return '*' in type
