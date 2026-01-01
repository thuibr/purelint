# purelint
Excessive mutability checking for Python. This is a Pylint plugin.

I have been learning Haskell and Gleam, but those are not languages that I use in production.
The motivation behind this project is to see how far I can get adding functional constraints to Python
and see what I can actually build.


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

Without the no mutable literal checker, which is very strict and makes you convert everything to immutable versions:
```
pylint --load-plugins=purelint --disable=no-mutable-literal-checker example.py
```

This is a design question I am still pondering. Do we want to keep the mutable literal checker or simply enforce that
lists/dicts/sets are never mutated after creation?

## Testing

```
uv run pytest
```
