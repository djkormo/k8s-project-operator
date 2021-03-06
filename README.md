# Kubernetes-operator


Kubernetes operator for maintaning 
projects, 
namespaces, 
resourcequotas, 
limitranges, 
networkpolicies, RBAC permissions 



```mermaid
flowchart LR;
    Project--create/update-->Namespace
    Project--create/update/delete-->ResourceQuota
    Project--create/update/delete-->LimitRange
    Project--create/update/delete-->NetworkPolicy

    NetworkPolicy-->allow-all-in-namespace
    NetworkPolicy-->allow-dns-access
    NetworkPolicy-->default-deny-egress
    NetworkPolicy-->default-deny-ingress


```



Add release version as git tag
```
git tag 0.0.6
git push origin --tags
```

HELM

```
helm repo add  djkormo-project https://djkormo.github.io/k8s-project-operator/

helm repo update

helm search repo project-operator  --versions

helm install project-operator djkormo-project/project-operator \
  --namespace project-operator --values charts/project-operator/values.yaml --create-namespace --dry-run

helm upgrade project-operator djkormo-project/project-operator \
  --namespace project-operator --values charts/project-operator/values.yaml


helm uninstall project-operator  --namespace project-operator 
```


Testing locally

```
helm lint charts/project-operator

helm template charts/project-operator -n project-operator --values charts/project-operator/values.yaml

```


```

kubectl -n project-operator logs deploy/project-operator -f
kubectl -n project-operator get events --sort-by=.metadata.creationTimestamp

```