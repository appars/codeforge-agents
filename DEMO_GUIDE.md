# 🎭 CodeForge Agents — Classroom Demo Script

Twelve verified demos arranged as a five-act show. Each one includes the
exact prompt to paste, what the class will see, and the one-line lesson
to land while it's on screen. Total runtime ≈ 30–40 minutes.

> Pre-flight: `.env` has your Groq key · `python -m rag.ingest` done ·
> sidebar shows 🟢 and "Index ready" · zoom the browser to ~125%.

---

## ACT 1 — Deterministic tools beat guessing

### Demo 1.1 — The tool is faster than the AI *(use the built-in card "🐍 Debug broken Python")*
**Watch for:** the Python Tool expander reports the SyntaxError with the exact
line — *before* any LLM reasoning happened.
**Say:** "The syntax error was caught by `compile()` — zero tokens, zero cost,
zero hallucination risk. The LLM only *explains*; the tool *knows*."

### Demo 1.2 — The infinite loop (the suspense demo) ⭐
Paste:
````
Debug this countdown, it never finishes:

```python
n = 10
while n > 0:
    print(n)
```
````
**Watch for:** the app pauses ~5 seconds (let the silence build!) then:
`⏱️ Execution killed after 5s (infinite loop?)`.
**Say:** "We just ran an infinite loop ON PURPOSE and the app survived.
The old version used `exec()` — this same demo would have frozen it forever.
This is what a tool guardrail is." Then show students the missing `n -= 1`.

### Demo 1.3 — Grounded by a real traceback
Paste:
````
Why does this crash?

```python
prices = {"apple": 30, "banana": 10}
print(prices["mango"])
```
````
**Watch for:** the tool captures the genuine `KeyError: 'mango'` stderr; the
Reviewer quotes it; the Synthesizer suggests `.get()` — and the RAG expander
shows the KeyError section retrieved from `python_debug.md`.
**Say:** "The agents aren't guessing the error — they read the actual stderr.
That's grounding."

---

## ACT 2 — The Router is smarter than keywords

### Demo 2.1 — The trap that broke v3 ⭐
Paste (no code at all):
```
My favourite equation is E = mc squared, can you explain it?
```
**Watch for:** Router says `general / explain` — **no tool fires**, and the
RAG expander reports *nothing relevant retrieved* (threshold doing its job).
**Say:** "The old keyword router saw `=` and ran this through the Python
executor. Knowing when NOT to act is agent intelligence too."

### Demo 2.2 — No hints given
Paste Java *without saying the word Java*:
````
Something's wrong here:

```java
public class Counter {
    public static void main(String[] args) {
        int total = 0
        for (int i = 1; i <= 5; i++) {
            total += i;
        }
        System.out.println(total);
    }
}
```
````
**Watch for:** Router classifies `java/debug` purely from the code shape;
the Java Tool flags the missing `;` on `int total = 0`.

---

## ACT 3 — RAG: knowledge the LLM cannot have

### Demo 3.1 — The killer demo *(use the built-in card "📚 Check team standards")* ⭐⭐
**Watch for:** the RAG expander retrieving `team_standards.md` chunks with
similarity scores, then the agents citing **K8-1** (no `team:` label),
**K8-2** (no resources), **K8-3** (`:latest`), **K8-4** (1 replica).
**Say:** "Ask ChatGPT about OUR team standards — it cannot know them. No
model on Earth trained on this file; it was written last week. THIS is why
RAG exists: private organizational knowledge."
**Bonus:** open `knowledge/team_standards.md` on screen and show the rules.

### Demo 3.2 — The negative control ⭐
Paste:
```
What is the capital of France?
```
**Watch for:** RAG expander: *no chunk passed the relevance threshold —
retrieving nothing is the CORRECT behavior.*
**Say:** "A naive RAG always injects its top-2 chunks — Java tips into a
geography question. Ours knows when its knowledge is irrelevant. In RAG
design, restraint is a feature."

### Demo 3.3 — Standards apply to Python too
Paste:
````
Does this follow our team standards?

```python
def load(path):
    try:
        f = open(path)
        return f.read()
    except:
        return "error: %s" % path
```
````
**Watch for:** agents citing **PY-3** (bare `except:`) and **PY-5**
(`%` formatting) from the retrieved standards — plus the unclosed file as a
bonus catch.

---

## ACT 4 — Bugs the compiler can't see

### Demo 4.1 — Compiles fine, still wrong ⭐
Paste:
````
This compiles but always prints "Access denied". Why?

```java
public class Login {
    public static void main(String[] args) {
        String user = new String("admin");
        if (user == "admin") {
            System.out.println("Welcome!");
        } else {
            System.out.println("Access denied");
        }
    }
}
```
````
**Watch for:** `javac` (if installed) passes it — yet the Reviewer catches
`==` comparing references, citing JV-3 from team standards via RAG.
**Say:** "Three layers just cooperated: the compiler said 'syntax fine', the
knowledge base said 'we ban == on Strings', the LLM connected them to YOUR
code. No single layer could do this alone."

### Demo 4.2 — The Norway problem 🇳🇴 ⭐
Paste:
````
Anything wrong with this ConfigMap?

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  country: no
  version: 3.10
```
````
**Watch for:** the YAML Tool says **Validation Passed** (it IS valid YAML!) —
then the agents, fed by the `yaml_k8s_debug.md` "Norway problem" chunk,
explain that `no` parsed as boolean `false` and `3.10` became the number
`3.1`. Fix: quote them.
**Say:** "Syntactically perfect, semantically broken — the scariest bug
class. The validator passed it; retrieval + reasoning caught it."

### Demo 4.3 — The invisible selector mismatch
Paste:
````
My pods never start, kubectl accepts the file though:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.25
          resources:
            requests: {cpu: 100m, memory: 128Mi}
            limits: {cpu: 500m, memory: 256Mi}
```
````
**Watch for:** structure checks pass — but `selector: app: webapp` ≠
`labels: app: web`, and the retrieved knowledge chunk is exactly about this.

---

## ACT 5 — Honesty, memory, and the finale

### Demo 5.1 — The honesty test ⭐
Paste:
````
Optimize this code:

```python
from collections import Counter

def top_words(text, n=3):
    return Counter(text.split()).most_common(n)

print(top_words('the cat and the dog and the bird'))
```
````
**Watch for:** the Optimizer replying **"No meaningful optimization needed."**
**Say:** "We prompted this agent to be allowed to say 'nothing to do'. An AI
that can say NO is more trustworthy than one that invents busywork. Prompt
design IS behavior design."

### Demo 5.2 — Memory across turns
After demo 1.2 (the countdown), simply type:
```
Now rewrite that same function to count down from any number the user enters, with input validation.
```
**Watch for:** the Synthesizer referencing the earlier countdown — the
memory window at work. Then drag the memory slider to 2, ask again about
"that function" several turns later, and watch it forget. **Limitation made
visible = lesson learned.**

### Demo 5.3 — The blackout finale ⭐⭐ (rehearse once!)
1. Stop the app. Rename the key: `mv .env .env.backup`
2. `streamlit run app.py` — badge turns 🔴, Tools-Only banner appears.
3. Click "🐍 Debug broken Python" → the SyntaxError is **still caught**,
   the knowledge **still retrieved** — only the agent prose is missing.
4. Restore: `mv .env.backup .env`, restart — 🟢 returns.

**Say:** "The LLM just died and the system kept working. Deterministic tools
are infrastructure; LLM reasoning is a layer on top. When you build agentic
systems, know which parts of your system survive an outage — because one day
it won't be a demo."

---

## Quick-reference: which demo teaches what

| Demo | Concept |
|---|---|
| 1.1–1.3 | tools-before-LLM, guardrails/timeouts, grounding |
| 2.1–2.2 | routing, knowing when NOT to act |
| 3.1–3.3 | RAG purpose, relevance thresholds, retrieval transparency |
| 4.1–4.3 | layered defenses, semantic vs syntactic bugs |
| 5.1 | honest agents via prompt design |
| 5.2 | memory windows and their limits |
| 5.3 | graceful degradation, system thinking |

## Pro tips
- **Open the expanders slowly** — the expanders ARE the lecture.
- After each demo, ask the class to predict the next one's pipeline path.
- Rate limits: if the class follows along live, everyone needs their own
  free Groq key — a shared key will 429 within minutes.
- If the Wi-Fi dies mid-class… congratulations, demo 5.3 just ran itself. 😄
