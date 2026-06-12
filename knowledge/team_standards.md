# CodeForge Inc. Engineering Standards (Internal)

<!--
TEACHING NOTE (for the instructor):
This file is the star of the RAG lesson. It contains FICTIONAL internal
rules that NO language model can know from training. When a student asks
"does this code follow our team standards?", the ONLY way the agent can
answer correctly is by retrieving this document.

To make the lesson personal: replace these rules with YOUR course's
actual submission/grading standards, re-run `python -m rag.ingest`,
and let students query the agent about your own rules.
-->

## Python standards
PY-1: Maximum line length is 100 characters (not PEP 8's 79).
PY-2: Every public function must have a docstring with at least one usage example.
PY-3: Bare `except:` clauses are forbidden — always catch a specific exception type.
PY-4: All new modules must include type hints on public function signatures.
PY-5: Use f-strings for formatting; `%` formatting and `.format()` are not allowed in new code.

## Java standards
JV-1: Every public class and public method requires a Javadoc comment.
JV-2: Class fields must be `private`; expose state only through methods.
JV-3: String comparisons must use `.equals()` — `==` on Strings fails code review automatically.
JV-4: Magic numbers are forbidden: any literal other than -1, 0, 1 must be a named constant.

## Kubernetes standards
K8-1: Every Deployment must carry a `team:` label identifying the owning team (e.g. `team: forge-platform`).
K8-2: Every container must define resource requests AND limits — manifests without them are rejected by CI.
K8-3: The `:latest` image tag is banned in all environments including dev.
K8-4: Every Deployment must run at least 2 replicas in production namespaces.
K8-5: All Secrets must come from the vault sync — inline base64 Secret manifests fail review.

## Review process
RV-1: All merge requests need one approval from a senior engineer; changes touching `core/` need two.
RV-2: A failing CI pipeline blocks merge — no exceptions, including "urgent" fixes.
RV-3: Review comments are resolved by the AUTHOR, never dismissed by the reviewer.
