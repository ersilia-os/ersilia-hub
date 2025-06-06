helm template ersilia-hub . --namespace ersilia-core --values values.secret.yaml > output.yaml
kubeconform output.yaml

read -p "Apply to cluster [N/y]? " should_apply

if ! [ -z "$should_apply" ] && [ "$should_apply" = "y" -o "$should_apply" = "Y" ]; then
    kubectl apply -f output.yaml -n ersilia-core
fi
