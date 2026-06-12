# 🚀 Deploying CodeForge Agents

One golden rule everywhere: **the image/repo carries the lock, never the
key.** `.env` is for your laptop only — every platform below injects
`GROQ_API_KEY` at runtime through its own secret mechanism, and
`core/config.py` reads whichever one is present. The app code never knows
or cares which platform it's on.

| Platform | Secret mechanism | Knowledge index |
|---|---|---|
| Laptop | `.env` file | `python -m rag.ingest` once |
| Docker | `-e` / `--env-file` at runtime | **baked into the image at build** |
| Kubernetes | `Secret` + `envFrom` | already in the image |
| Streamlit Cloud | Secrets panel (`st.secrets`) | sidebar 📚 button after deploy |

---

## 1. Docker

```bash
# Build — note: NO key needed at build time. rag.ingest only does local
# chunking + embeddings, so the index is baked in with zero secrets.
docker build -t codeforge-agents:4.3 .

# Run — key injected at runtime (pick one):
docker run -p 8501:8501 -e GROQ_API_KEY='gsk_...' codeforge-agents:4.3
docker run -p 8501:8501 --env-file .env codeforge-agents:4.3   # file stays on host

# open http://localhost:8501
```

Why this is safe: `.dockerignore` excludes `.env`, `venv/`, `.git/` from
the build context, so the image physically cannot contain your key —
verify it yourself: `docker run --rm codeforge-agents:4.3 ls -la /app`
(no `.env` listed). You can push this image to any registry without worry.

Classroom corner case: run it **without** the key —
`docker run -p 8501:8501 codeforge-agents:4.3` — and show students the
🔴 Tools-Only Mode working in a container. Graceful degradation survives
containerization.

---

## 2. Kubernetes

```bash
# Step 1 — the key lives in the CLUSTER, never in a YAML file (K8-5!)
kubectl create secret generic codeforge-secrets \
    --from-literal=GROQ_API_KEY='gsk_your_key_here'

# Step 2 — deploy (2 replicas, probed, resource-limited, non-root)
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Step 3 — reach it
kubectl port-forward svc/codeforge-agents 8501:8501
```

If you build the image locally for minikube/kind, load it first:
`minikube image load codeforge-agents:4.3` (or `kind load docker-image …`).

**The meta-lesson 🤯:** `k8s/deployment.yaml` deliberately satisfies every
rule in `knowledge/team_standards.md` (team label, resources, pinned tag,
2 replicas, cluster-managed secret). In class: paste the manifest into
CodeForge Agents itself and ask *"does this follow our team standards?"* —
the app reviews its own deployment. Then delete the `team:` label and ask
again.

Rotating the key later:
```bash
kubectl delete secret codeforge-secrets
kubectl create secret generic codeforge-secrets --from-literal=GROQ_API_KEY='gsk_NEW'
kubectl rollout restart deployment codeforge-agents
```

---

## 3. Streamlit Community Cloud

1. Push the repo to GitHub — **verify `.env` is not in it**:
   `git ls-files | grep .env` must show only `.env.example`.
2. share.streamlit.io → New app → pick your repo, branch `main`, file `app.py`.
3. App → **Settings → Secrets** → paste:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
   `core/config.py` finds it automatically via `st.secrets` (env vars are
   checked first, so the same code runs on every platform unchanged).
4. After first boot, click **📚 Build Knowledge Base** in the sidebar
   (~1 minute: downloads the embedding model and indexes 43 chunks).

Cloud quirks to know: the filesystem is **ephemeral** — after the app
sleeps or redeploys, the index is gone; just click 📚 again. Ollama
obviously isn't available there, so the fallback chain is simply
Groq → Tools-Only Mode.

---

## The security checklist (worth a slide)

- [ ] `.env` in `.gitignore` ✓ and `.dockerignore` ✓
- [ ] `git ls-files | grep "\.env$"` returns nothing
- [ ] Zips/shares never include `.env`, `venv/`, `.git/`
- [ ] K8s key via `kubectl create secret`, never inline YAML
- [ ] If a key ever travels (zip, screenshot, commit): **rotate it
      immediately** at console.groq.com/keys — rotation takes 60 seconds,
      regret lasts longer.
