# Kubernetes Best Practices

## Always set resource requests and limits
Every container should declare `resources.requests` (what the scheduler reserves) and `resources.limits` (the hard ceiling). Without requests, the scheduler packs pods blindly and one greedy pod can starve a node. Reasonable starter values for a small web service: requests `cpu: 100m, memory: 128Mi`; limits `cpu: 500m, memory: 256Mi`.

## Health probes — liveness vs readiness
`livenessProbe` answers "is the process stuck?" — failing it RESTARTS the container.
`readinessProbe` answers "can it serve traffic right now?" — failing it removes the pod from the Service endpoints WITHOUT restarting it.
Use readiness for slow startup and warm-up; use liveness only for genuine deadlock detection. A too-aggressive liveness probe on a slow-starting app causes an endless restart loop.

## Never use the :latest tag
`image: myapp:latest` makes deployments non-reproducible: you cannot tell what is actually running, and rollback becomes meaningless. Pin a version (`myapp:1.4.2`) or better, a digest. Set `imagePullPolicy: IfNotPresent` for pinned tags.

## Labels and selectors
Give every object a consistent label set, minimally `app:` and ideally the recommended `app.kubernetes.io/name`, `app.kubernetes.io/version`. Labels power Service routing, Deployment pod ownership, `kubectl get -l` filtering, and monitoring dashboards. Inconsistent labels are the root cause of "my Service has no endpoints".

## Don't run as root
Set a `securityContext` with `runAsNonRoot: true` and a numeric `runAsUser`. Add `allowPrivilegeEscalation: false` and drop capabilities you don't need. A container compromise should not hand over the node.

## Configuration belongs outside the image
Environment-specific values go in ConfigMaps; secrets (passwords, tokens, keys) go in Secrets — never baked into the image and never committed to git in plain text. Mount or inject them via `envFrom` / volume mounts so one image runs in every environment.

## Set replicas and a sane update strategy
For anything user-facing, `replicas: 2` minimum so one pod can die or be rescheduled without an outage. The default RollingUpdate strategy with `maxUnavailable: 0, maxSurge: 1` gives zero-downtime deploys for small services.
