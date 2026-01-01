# purelint
Excessive mutability checking for Python. This is a Pylint plugin.

I have been learning Haskell and Gleam, but those are not languages that I use in production.
The motivation behind this project is to see how far I can get adding functional constraints to Python
and see what I can actually build.

## Features

- `match` exhaustiveness checker


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
