# Details #

## Docker Images ##

Both the server and frontend docker images are built and published using GitHub Actions:
- [build-frontend.yaml](../.github/workflows/build-frontend.yaml)
- [build-server.yaml](../.github/workflows/build-server.yaml)

Currently, versioning is done **manually**, so you need to update the version hardcoded in the relevant GitHub action file before releasing a new version.\
Failing to do this might lead to overwriting an exisiting image and this could cause issues in the live environment.

## Helm charts ##

The deployment to kubernetes is done using a [Helm chart](../operations/helm/).\
The Helm chart implementation is fairly generic and mostly only changes to the [values.yaml](../operations/helm/values.yaml) will be required.\

If a new version of the frontend or server is published, you can change the deployed version in the [values.yaml](../operations/helm/values.yaml) and [execute the deployment](#helm-deployment).

Similarly, for server environment variable changes, these should be set in the [values.yaml](../operations/helm/values.yaml) file and deployed.

## Helm deployment ##

There is a deployment script [operations/deploy.sh](../operations/deploy.sh) which should be used to deploy the frontend and server to the live environment.\
The script will:
- perform Helm dependency updates (if required)
- render the Kubernetes helm chart into Kubernetes yaml artifacts
- validate the Kubernetes artifacts
- apply the resources to the kubernetes cluster.

```
cd operations
./deploy.sh
```

---

# How to Deploy #

1. Make changes to the frontend and/or server code
2. Update the version(s) in the GitHub Action workflows
3. Deploy images using github actions (automated on push to main branch)
4. Update the image versions or environment variables in the Helm values.yaml file
5. Deploy the helm chart
6. Monitor pods in kubernetes and ensure deployment was successful.
7. Do some testing


