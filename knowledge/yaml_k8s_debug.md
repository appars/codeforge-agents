# YAML and Kubernetes Debugging Reference

## Tabs are illegal in YAML
Error: `found character '\t' that cannot start any token`.
Cause: YAML forbids tab characters for indentation entirely.
Fix: replace every tab with spaces (2 spaces per level is the Kubernetes convention). Configure your editor: "insert spaces for tab".

## Missing colon after a key
Error: `could not find expected ':'` or `mapping values are not allowed here`.
Cause: a line like `name my-app` instead of `name: my-app`, or a value containing an unquoted `:` (URLs are the classic trap).
Fix: every key needs `key: value`. Quote values containing colons: `url: "http://example.com:8080"`.

## Indentation defines structure
Symptom: the file parses, but a field "disappears" — e.g. `kubectl` says `metadata.name` is missing although you can see it.
Cause: wrong indentation level placed the key inside the WRONG parent (e.g. `name` indented under `labels` instead of under `metadata`).
Fix: each nesting level is exactly 2 spaces deeper than its parent; sibling keys align at the same column. Validate fast with: `python -c "import yaml,sys; print(yaml.safe_load(open(sys.argv[1])))" file.yaml`.

## Required Kubernetes fields
Every manifest needs four top-level fields: `apiVersion`, `kind`, `metadata` (with at least `name`), and for most kinds a `spec`.
kubectl error `error: unable to decode ... no kind "deployment"` → `kind` values are CASE-SENSITIVE: `Deployment`, not `deployment`.
`error validating data: unknown field` → usually a typo (`replica:` vs `replicas:`) or a field at the wrong indentation level.

## Deployment selector must match template labels
Error: `spec.template.metadata.labels: Invalid value ... does not match spec.selector`.
Cause: in a Deployment, `spec.selector.matchLabels` MUST be a subset of `spec.template.metadata.labels` — that is how the Deployment finds its own pods.
Fix: make them identical, e.g. both `app: my-app`.

## CrashLoopBackOff
Meaning: the container starts, crashes, and Kubernetes keeps restarting it with growing delays.
Diagnose: `kubectl logs <pod> --previous` shows the output of the crashed attempt (the current one may be empty). Common causes: application error on startup, missing env var/config, wrong command, or failing liveness probe killing a slow-starting app.

## ImagePullBackOff / ErrImagePull
Meaning: the node cannot download the container image.
Causes in order of frequency: typo in the image name or tag, the tag does not exist, the registry is private and no imagePullSecret is configured.
Diagnose: `kubectl describe pod <pod>` — the Events section at the bottom states the exact pull error.

## Quoting surprises (the Norway problem)
Unquoted `no`, `yes`, `on`, `off`, `true`, `false` parse as booleans, and `3.10` parses as the number 3.1. So `country: no` becomes `country: false`!
Fix: quote ambiguous scalars: `country: "no"`, `version: "3.10"`.
