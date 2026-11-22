# Lab 13.2 - Kubernetes StatefulSet

The manifests define a three-member MongoDB StatefulSet, a headless Service,
one 5 GiB PVC per pod, readiness/liveness probes, an init container that copies
the same Secret keyfile into a memory-backed volume with owner `999:999` and
mode `0400`, and a Job that initializes `rs0`. Credentials and key material
must be supplied as Kubernetes Secrets and are intentionally excluded here.

## Prerequisites and deploy

Use a cluster with a default StorageClass and sufficient storage. In Docker
Desktop, enable Kubernetes first if it is available. From this directory:

```sh
kubectl cluster-info
kubectl create namespace mongo-lab --dry-run=client -o yaml | kubectl apply -f -
cd ../Lab-13.1-Docker
./generate-keyfile.sh
cd ../Lab-13.2-Kubernetes
kubectl -n mongo-lab create secret generic mongo-keyfile \
  --from-file=keyfile=../Lab-13.1-Docker/secrets/keyfile
kubectl -n mongo-lab create secret generic mongo-auth \
  --from-literal=username="$(sed -n 's/^MONGO_INITDB_ROOT_USERNAME=//p' ../Lab-13.1-Docker/.env)" \
  --from-literal=password="$(sed -n 's/^MONGO_INITDB_ROOT_PASSWORD=//p' ../Lab-13.1-Docker/.env)"
kubectl apply -n mongo-lab -f mongo-headless-svc.yaml
kubectl apply -n mongo-lab -f mongo-statefulset.yaml
kubectl -n mongo-lab rollout status statefulset/mongo --timeout=10m
kubectl apply -n mongo-lab -f mongo-init.yaml
kubectl -n mongo-lab wait --for=condition=complete job/mongo-init-rs --timeout=5m
```

Both secrets contain sensitive data. Create them only in a trusted cluster and
avoid shell history in a shared environment. For production, enable Kubernetes
encryption at rest and use an external secret manager.

## Verify and recovery test

```sh
kubectl -n mongo-lab get pods,pvc
kubectl -n mongo-lab exec mongo-0 -- sh -ec \
  'mongosh --quiet -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "rs.status().members.map(m => ({name:m.name,stateStr:m.stateStr}))"'
kubectl -n mongo-lab delete pod mongo-1
kubectl -n mongo-lab wait --for=condition=Ready pod/mongo-1 --timeout=5m
kubectl -n mongo-lab get pods,pvc
```

The StatefulSet recreates the deleted pod with the same stable identity and
reattaches its PVC. Confirm that `rs.status()` shows it recovered as a
`SECONDARY`. These checks require a live cluster and are not represented as
completed unless actually run.

To clean up: `kubectl delete namespace mongo-lab` (PVC reclaim behavior depends
on the cluster's StorageClass).
