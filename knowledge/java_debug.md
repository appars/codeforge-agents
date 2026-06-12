# Java Debugging Reference

## error: ';' expected
Compiler output: `Test.java:5: error: ';' expected`.
Cause: every Java statement ends with a semicolon — assignments, method calls, `return`, declarations.
Fix: add `;` at the reported line. Watch out: the compiler sometimes reports the line AFTER the real omission, because that is where parsing actually broke.

## class X is public, should be declared in a file named X.java
Cause: in Java, a `public` class name must exactly match its filename, including capitalization.
Fix: rename the file or the class so they match: `public class HelloWorld` lives in `HelloWorld.java`. Only ONE public class per file.

## error: reached end of file while parsing
Cause: unbalanced braces — usually a missing `}` at the end of a method or class.
Fix: count `{` vs `}`. Indent consistently so each closing brace visually aligns with its opener; most IDEs highlight the matching brace when you place the cursor on one.

## NullPointerException (NPE)
Runtime: `Exception in thread "main" java.lang.NullPointerException` with a stack trace.
Cause: calling a method or field on a reference that is `null` — commonly an uninitialized field, a map `get()` that returned null, or a method that can return null.
Fix: the FIRST line of the stack trace pointing into your own code is the crime scene. Guard with `if (obj != null)`, use `Objects.requireNonNull(obj, "message")` to fail fast with a clear message, or return `Optional<T>` from methods that may have no result.

## cannot find symbol
Compiler: `error: cannot find symbol — symbol: variable total`.
Causes: typo in the name, using a variable outside the block where it was declared (Java scoping is per-block), or a missing import.
Fix: declare the variable in the outermost scope where it is needed. For classes: add the import (`import java.util.List;`) — the compiler tells you exactly which symbol it cannot resolve.

## error: incompatible types
Example: `error: incompatible types: String cannot be converted to int`.
Cause: Java is statically typed — assignments must match declared types.
Fix: convert explicitly: `int n = Integer.parseInt(text);` and the reverse `String s = String.valueOf(n);`. Beware integer division: `5 / 2` is `2`; write `5 / 2.0` for `2.5`.

## main method signature
A runnable class needs EXACTLY: `public static void main(String[] args)`.
Wrong signatures (`static public void Main`, missing `String[] args`, lowercase `string`) compile fine as ordinary methods but the JVM reports: `Error: Main method not found in class`.

## == vs .equals() for Strings
`if (name == "admin")` compares object REFERENCES, not contents — it may pass in tests (string pooling) and fail in production.
Fix: always `name.equals("admin")`, or null-safe: `"admin".equals(name)`.
