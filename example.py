"""Examples"""

x = 1
x = 2
Y = 1
print(Y)

a = 1
a += 1

with open(__file__, "r") as f:
    pass

open(__file__)


f = list()  # triggers mutable-literal-used
g = dict()  # triggers mutable-literal-used
h = set()  # triggers mutable-literal-used
i = []  # triggers mutable-literal-used
j = {}  # triggers mutable-literal-used
k = {1, 2}  # triggers mutable-literal-used


def f1():
    conn = 1
    return conn


def f2():
    conn = 2
    return conn
