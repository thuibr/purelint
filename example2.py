"""Docstring"""

from copy import deepcopy

import requests

from purelint import pipe

resp = requests.get("https://pokeapi.co/api/v2/pokemon/ditto", timeout=5)
resp.raise_for_status()

body = resp.json()

body["abilities"] = None

new_body = pipe(
    deepcopy(body), lambda b: {k: v for k, v in b.items() if k != "abilities"}
)
print(new_body)

new_body2 = body
del new_body2["abilities"]

lst = [5]
lst[0] = 1
lst.pop()
del lst[0]


class Obj:
    def __init__(self):
        self.attr = "hi"


obj = Obj()
del obj.attr
del obj
