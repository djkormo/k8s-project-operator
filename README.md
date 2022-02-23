Kubernetes operator for maintaning projects, namespaces, resourcequotas, limitranges, resourceqotas, networkpolicies, RBAC permissions 

Kubernetes operator for maintaning 
projects, 
namespaces, 
resourcequotas, 
limitranges, 
networkpolicies, RBAC permissions 



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

```yaml
apiVersion: djkormo.github/v1alpha2
kind: Project
metadata:
  name: my-namespace
  namespace: project-operator
  # sample labels
  labels:
    owner: "djkormo"
    type: "operator"
    env: "kubernetes"
    name: "project"
  # sample annotations 
  annotations:
    project-operator/multiline.pattern: "test-paterrn"
    project-operator/multiline.name: "test-name"
spec:
  # resourcequota
  resourcequota:
    resourcequotarequestscpu: "4"
    resourcequotarequestsmemory: 5Gi
    resourcequotalimitscpu: "3"
    resourcequotalimitsmemory: 4Gi
    resourcequotacountjobsbatch: 4k
    resourcequotacountingresses: 2k
    resourcequotapods: "109"
    resourcequotaservices: "109"
    resourcequotaconfigmaps: "100"
    resourcequotapersistentvolumeclaims: "98"
    resourcequotareplicationcontrollers: "97"
    resourcequotasecrets: "96"
    resourcequotaservicesloadbalancers: "102"
  # limit range  
  limitrange:
    limitrangemaxcpu: 20000m
    limitrangemaxmem: "20Gi"
    limitrangemincpu: "50m"
    limitrangeminmem: "50Mi"
    limitrangedefaultcpu: "1000m"
    limitrangedefaultmem : "1000Mi"
    limitrangedefaultrequestcpu: "100m"
    limitrangedefaultrequestmem: "100Mi"
  # networkPolicy
  networkpolicy:
    - allow-all-in-namespace
    - allow-dns-access
    - default-deny-egress
    - default-deny-ingress
  # rbac, role, rolebinding
  rbac: {}
```
