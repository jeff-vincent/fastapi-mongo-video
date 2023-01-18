# fastapi-mongo-video

## Run in Minikube
```shell
minikube start
minikube addons enable kong
minikube tunnel
```
```shell
cd fastapi-mongo-video/k8s
helm template . --values values.yaml | kubectl apply -f -
```

## Run in Velocity
```shell
cd fastapi-mongo-video/k8s
helm template . --values velocity-values.yml | veloctl env create -f -
```
