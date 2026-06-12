"""
CodeForge Agents — YAML / Kubernetes Tool
=========================================
Two layers of deterministic validation:

    1. SYNTAX    — yaml.safe_load (the parser is the source of truth)
    2. STRUCTURE — Kubernetes-specific checks (apiVersion, kind,
                   metadata.name, container images, resource limits…)

The structure layer only fires when the document LOOKS like a K8s
manifest, so plain YAML config files are not nagged about `kind`.
"""

import yaml

from tools.extract import extract_yaml


def _k8s_checks(doc: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings) for one Kubernetes document."""
    errors, warnings = [], []

    for field in ("apiVersion", "kind", "metadata"):
        if field not in doc:
            errors.append(f"Missing required field `{field}`.")

    md = doc.get("metadata")
    if md is not None:
        if not isinstance(md, dict):
            errors.append("`metadata` must be a mapping (key: value block) — "
                          "a missing `:` often causes this.")
        elif "name" not in md:
            errors.append("Missing `metadata.name`.")

    kind = str(doc.get("kind", ""))
    spec = doc.get("spec", {})

    if kind in ("Deployment", "StatefulSet", "DaemonSet", "Pod", "Job"):
        # Locate the pod spec (direct for Pod, nested via template otherwise)
        pod_spec = spec if kind == "Pod" else (
            spec.get("template", {}) or {}).get("spec", {})
        containers = (pod_spec or {}).get("containers") or []
        if not containers:
            errors.append(f"`{kind}` has no containers defined.")
        for c in containers:
            if not isinstance(c, dict):
                continue
            cname = c.get("name", "<unnamed>")
            if "image" not in c:
                errors.append(f"Container `{cname}` is missing `image`.")
            if "resources" not in c:
                warnings.append(f"Container `{cname}` has no resource "
                                "requests/limits (best practice).")
            if "livenessProbe" not in c:
                warnings.append(f"Container `{cname}` has no livenessProbe "
                                "(best practice).")
        if kind == "Deployment":
            if "selector" not in spec:
                errors.append("Deployment is missing `spec.selector`.")
            if "replicas" not in spec:
                warnings.append("No `replicas` set — defaults to 1.")
    return errors, warnings


def run(text: str) -> dict:
    yml = extract_yaml(text)
    if not yml:
        return {"ok": False, "title": "☸️ YAML Tool",
                "output": "No YAML content detected — passing the text "
                          "straight to the agents.",
                "code": ""}

    # ---- Layer 1: syntax ------------------------------------------------
    try:
        docs = [d for d in yaml.safe_load_all(yml) if d is not None]
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        loc = f" (line {mark.line + 1}, column {mark.column + 1})" if mark else ""
        return {"ok": False, "title": "☸️ YAML Tool — Syntax Error",
                "output": f"❌ YAML parse error{loc}:\n{e}\n\n"
                          "Common causes: tabs instead of spaces, missing "
                          "`:` after a key, or misaligned indentation.",
                "code": yml}

    if not docs:
        return {"ok": False, "title": "☸️ YAML Tool",
                "output": "Parsed, but the document is empty.", "code": yml}

    # ---- Layer 2: Kubernetes structure -----------------------------------
    report, all_ok = [], True
    for i, doc in enumerate(docs, 1):
        label = f"Document {i}" if len(docs) > 1 else "Document"
        if not isinstance(doc, dict):
            report.append(f"❌ {label}: top level must be a mapping.")
            all_ok = False
            continue
        looks_k8s = "apiVersion" in doc or "kind" in doc
        if not looks_k8s:
            report.append(f"✅ {label}: valid YAML (not a Kubernetes "
                          "manifest — skipping K8s checks).")
            continue
        errors, warnings = _k8s_checks(doc)
        if errors:
            all_ok = False
            report.append(f"❌ {label} ({doc.get('kind', '?')}): "
                          + "; ".join(errors))
        else:
            report.append(f"✅ {label} ({doc.get('kind', '?')}): structure OK.")
        for w in warnings:
            report.append(f"  ⚠️ {w}")

    title = "☸️ YAML Tool — " + ("Validation Passed" if all_ok
                                 else "Issues Found")
    return {"ok": all_ok, "title": title, "output": "\n".join(report),
            "code": yml}
