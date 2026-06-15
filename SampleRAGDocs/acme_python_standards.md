# Acme Python Engineering Standards

## Naming
Use snake_case for functions and variables, PascalCase for classes.
Avoid single-letter names except loop counters i, j, k.

## Type hints and docstrings
Every public function MUST have full type hints and a Google-style
docstring. A function with no type hints fails the Acme CI lint gate.

## Logging
Never use print() in committed code. Use the structured logger
acme.log.get_logger(__name__). print() statements are blocked by our
pre-commit hook.

## Loops and performance
Avoid nested loops over large collections. Prefer dict/set lookups (O(1))
to repeated list membership tests (O(n)). Cap any single function at
cyclomatic complexity 10.

## Error handling
Catch specific exceptions, never a bare `except:`. Log the exception with
context before re-raising.
