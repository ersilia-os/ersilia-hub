helm template ersilia-hub . --namespace eos-models > output.yaml
kubeconform output.yaml

read -p "Apply to cluster [N/y]? " should_apply

if ! [ -z "$should_apply" ] && [ "$should_apply" = "y" -o "$should_apply" = "Y" ]; then
    kubectl apply -f output.yaml -n eos-models
fi