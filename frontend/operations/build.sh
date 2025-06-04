npm ci
npm run build

docker build . -t $IMAGE:$VERSION