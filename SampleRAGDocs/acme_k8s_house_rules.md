# Acme Kubernetes House Rules

## Image tags
Never deploy with the `latest` tag. Always pin an explicit version such as
:4.7. Unpinned images are rejected by the Acme admission controller.

## Resource requests and limits
Every container must declare both resource requests and limits. A pod with
no limits can starve the node and is blocked from the production cluster.

## Security context
Containers must run as non-root (runAsNonRoot: true) with a numeric UID.
Never mount the Docker socket and never set privileged: true.

## Secrets
Inject secrets from the cluster with secretRef. Never write a secret inline
in the manifest or bake it into the image. Rotate on any exposure.

## Reliability
Set readiness and liveness probes on every Deployment, and run at least two
replicas for anything user-facing.
