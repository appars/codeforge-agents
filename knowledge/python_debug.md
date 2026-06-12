# Python Debugging Reference

## SyntaxError — missing colon
Error: `SyntaxError: expected ':'` pointing at a `for`, `if`, `while`, `def` or `class` line.
Cause: Python block statements must end with a colon.
Fix: `for i in range(5):` ← add the colon, then indent the body.
Note: The reported line number is usually exact for missing colons, but for unclosed brackets Python may point one line BELOW the real mistake.

## IndentationError and TabError
Error: `IndentationError: expected an indented block` or `TabError: inconsistent use of tabs and spaces`.
Cause: The line after a `:` is not indented, or the file mixes tabs with spaces.
Fix: Use 4 spaces per level, never tabs. Configure your editor to insert spaces for the Tab key. To find a stray tab: search the file for the literal `\t` character.

## NameError — name is not defined
Error: `NameError: name 'x' is not defined`.
Cause: Using a variable before assignment, a typo in the name, or a variable created inside a function/branch that never executed.
Fix: Check spelling and definition order. A frequent classroom case: defining a variable inside an `if` branch that did not run, then using it after the `if`. Initialize before the branch.

## TypeError — common shapes
`TypeError: can only concatenate str (not "int") to str` → convert with `str(n)` or use an f-string: `f"count: {n}"`.
`TypeError: 'NoneType' object is not subscriptable` → a function returned `None` (often a missing `return` statement) and you indexed the result.
`TypeError: f() missing 1 required positional argument` → check the call against the function signature, including `self` in methods.

## IndexError and KeyError
`IndexError: list index out of range` → remember the last valid index is `len(lst) - 1`; off-by-one loops like `range(len(lst) + 1)` are the classic cause.
`KeyError: 'name'` → the dict has no such key; use `d.get('name')` to receive `None` instead of crashing, or check `if 'name' in d:` first.

## ImportError and ModuleNotFoundError
Error: `ModuleNotFoundError: No module named 'pandas'`.
Cause: The package is not installed in the CURRENT interpreter/virtualenv — often it was installed globally but you are running inside a venv (or vice versa).
Fix: Activate the right environment, then `pip install pandas`. Verify which interpreter runs with `python -c "import sys; print(sys.executable)"`.

## Infinite loops
Symptom: program hangs, no error.
Cause: a `while` condition that never becomes false, e.g. forgetting to increment the counter, or mutating the wrong variable.
Fix: ensure something inside the loop moves the condition toward false. Defensive pattern for student code: add a max-iterations guard while debugging.

## Reading a traceback
Read the traceback BOTTOM-UP: the last line names the exception and message; the lines above show the call chain, most recent call last. The deepest frame in YOUR code (not library code) is where to look first.
