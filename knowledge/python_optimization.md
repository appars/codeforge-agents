# Python Optimization Reference

## Measure before optimizing
Rule one: profile first. Use `time.perf_counter()` around suspect blocks, or `python -m cProfile script.py` for a full picture. Optimizing unmeasured code wastes effort on the wrong 90%.

## Loops — the usual wins
Membership tests: `x in my_list` is O(n); convert to a set once (`s = set(my_list)`) for O(1) lookups inside loops.
String building: never `result += piece` inside a loop (quadratic). Collect into a list and `''.join(parts)` once.
List building: a comprehension `[f(x) for x in xs]` is faster and clearer than append-in-a-loop.

## Generators vs lists
`sum(x*x for x in range(10**7))` streams values one at a time — near-zero memory. The list version materializes everything first. Prefer generator expressions when you only iterate once; prefer lists when you need indexing or multiple passes.

## Nested loops — rethink the data structure
An O(n²) double loop matching items between two lists usually becomes O(n) with a dict: build `index = {item.key: item for item in list_b}` once, then look up inside the single loop over `list_a`.

## Caching repeated computation
For pure functions called repeatedly with the same arguments, `from functools import lru_cache` and decorate with `@lru_cache(maxsize=None)`. Classic demo: naive recursive Fibonacci goes from exponential to linear with one decorator line.

## Built-ins beat hand-rolled code
`sum`, `min`, `max`, `sorted`, `any`, `all`, `collections.Counter` are implemented in C. A hand-written counting loop is typically 5–10x slower than `Counter(items)` and easier to get wrong.

## When NOT to optimize
If the code runs once, finishes in milliseconds, or readability would suffer for a 2% gain — leave it. Clear code that students can review is worth more than clever code. State explicitly when no optimization is warranted.
