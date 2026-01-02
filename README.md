# purelint
Excessive mutability checking for Python. This is a Pylint plugin.

I have been learning Haskell and Gleam, but those are not languages that I use in production.
The motivation behind this project is to see how far I can get adding functional constraints to Python
and see what I can actually build.

## Features

- `match` exhaustiveness checker, ensuring that all `match` statements have a `_` clause
  - It is recommended to use something like `assert_never(value)` so that type checkers like `mypy` pick up on any unmatched cases
    For example:
    ```python
    from typing import assert_never

    def taker(v: Animal | None | int):
        """Check animal lint"""
        match v:
            case None:
                pass
            case Animal():
                pass
            case int():
                pass
            case _:
                assert_never(v)
    ```
    Then run `mypy` on your code. It will give you an error if you're not checking all cases.
- Variable rebinding
- No augmented assignments
- No mutable methods
- No subscript assignment
- No deletes
- A `pipe` tool for immutable transformations on a data structure
  For example:
  ```python
  from purelint import pipe
  
  sorted_after_deletes = pipe(
      build_tree(values),  # start with tree
      lambda t: delete(t, 2),  # delete 2
      lambda t: delete(t, 5),  # delete 5
      inorder,  # get sorted tuple
  )
   ```


## Installing

With `uv`:
```
uv add --dev purelint
```

With `pip`:
```
pip install -U purelint
```

## Running

```
pylint --load-plugins=purelint example.py
```

With `uv`:
```
uv run pylint --load-plugins=purelint example.py
```

## Testing

```
uv run pytest
```
