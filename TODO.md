[ ] github actions build for server
[ ] github actions build for frontend

[ ] helm manifest for server deployment
[ ] helm manifest for frontend deployment

[ ] configure IRSA for server
    - only S3 access for now
[ ] configure k8s RBAC for server Service Account
    - all Pod and PodTemplate actions in eos-models namespace

[ ] deploy postgres server to k8s
    [ ] configure EBS PVC
    [ ] configure secrets
    [ ] use bitnami postgres helm chart