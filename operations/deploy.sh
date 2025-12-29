WD=$PWD
DEPLOYMENTS_DIR="$WD/.deployments"
DEPLOYMENT_NAME=$(date -u +'%Y-%m-%d_%H-%M')
DEPLOYMENT_NAMESPACE="ersilia-core"
HELM_PATH="helm"

mkdir -p $DEPLOYMENTS_DIR

cd $HELM_PATH

helm dependency update

echo "Render deployment template..."
helm template ersilia-hub . --namespace $DEPLOYMENT_NAMESPACE --dry-run=server > $DEPLOYMENTS_DIR/$DEPLOYMENT_NAME.yaml

echo "Validate deployment..."
kubeconform -summary -ignore-missing-schemas $DEPLOYMENTS_DIR/$DEPLOYMENT_NAME.yaml

if [ "$?" != "0" ]; then
  echo "Template validation failed! Stopping installation."
  exit 1
fi

read -p "Apply changes? [Y/N] " apply

if [ $apply = "Y" ] || [ $apply = "y" ]; then
  echo "Applying deployment..."
  kubectl apply -f $DEPLOYMENTS_DIR/$DEPLOYMENT_NAME.yaml
else
  echo "Exiting..."
fi

###
# NOTE: push to git is removed, but should be safe to add.
#       We should not store any secrets in code (i.e. this repo), so it should be safe to use, but only IFF you want to
###
# git add $DEPLOYMENTS_DIR/$DEPLOYMENT_NAME.yaml
# git add .
# git commit -m "chore: Deployment completed [$HELM_PATH - $DEPLOYMENT_NAME]"
# git push
