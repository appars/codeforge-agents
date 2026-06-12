"""
CodeForge Agents — Demo Scenarios
=================================
Six curated prompts, each exercising a DIFFERENT path through the agent
pipeline. Together they form a complete guided tour of the architecture —
your live demo script for the classroom.
"""

SCENARIOS = [
    {
        "label": "🐍 Debug broken Python",
        "path": "Router → Python Tool → Reviewer → Optimizer → Synthesizer",
        "prompt": """Debug this Python code, it's not working:

```python
for i in range(5)
    print(i)
```""",
    },
    {
        "label": "☸️ Fix a Kubernetes YAML",
        "path": "Router → YAML Tool → Reviewer → Synthesizer",
        "prompt": """My deployment won't apply, can you fix it?

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:latest
```""",
    },
    {
        "label": "☕ Review a Java class",
        "path": "Router → Java Tool (static checks) → Reviewer",
        "prompt": """Review this Java code for problems:

```java
public class Greeter {
    public static void main(String[] args) {
        String name = "world";
        if (name == "world") {
            System.out.println("Hello " + name)
        }
    }
}
```""",
    },
    {
        "label": "📚 Check team standards (RAG demo!)",
        "path": "Router → RAG retrieval (team_standards.md) → agents",
        "prompt": """Does this deployment follow our team standards?

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments-api
  labels:
    app: payments
spec:
  replicas: 1
  selector:
    matchLabels:
      app: payments
  template:
    metadata:
      labels:
        app: payments
    spec:
      containers:
        - name: payments
          image: payments:latest
```""",
    },
    {
        "label": "⚡ Optimize a nested loop",
        "path": "Router → Python Tool → Optimizer (shines here)",
        "prompt": """Can you optimize this? It's very slow on big lists:

```python
def find_common(list_a, list_b):
    common = []
    for a in list_a:
        for b in list_b:
            if a == b:
                common.append(a)
    return common

print(find_common([1, 2, 3, 4], [3, 4, 5, 6]))
```""",
    },
    {
        "label": "📖 Explain code (no tool fires)",
        "path": "Router (intent=explain) → RAG → Synthesizer",
        "prompt": """Explain what this code does, step by step:

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

print([fib(i) for i in range(10)])
```""",
    },
]
