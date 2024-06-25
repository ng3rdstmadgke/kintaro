# ■ terraformデプロイ
```bash
cd ${CONTAINER_PROJECT_ROOT}/terraform/env/prd
terraform init
terraform plan
terraform apply -auto-approve
```

# ■ dockerイメージのpush

```bash
cd $CONTAINER_PROJECT_ROOT
${CONTAINER_PROJECT_ROOT}/bin/build.sh --push prd
```

# ■ Kubenetesリソースのデプロイ

以下のファイルのイメージバージョンを更新します

- `kustomize/overlays/prd/app_deployment.patch.yaml`
- `kustomize/overlays/prd/crawler_cronjob.patch.yaml`
- `kustomize/overlays/prd/job_scaled_job.patch.yaml`


デプロイ

```bash
cd $CONTAINER_PROJECT_ROOT
kubectl apply -k ${CONTAINER_PROJECT_ROOT}/kustomize/overlays/prd/
```

リソースの確認

```bash
# 主要なリソース一覧
kubectl get all -n kintaro-prd

# ALBのURLを確認 
$ kubectl get ing -n kintaro-prd
NAME      CLASS   HOSTS   ADDRESS                                                                     PORTS   AGE
ingress   alb     *       k8s-producti-ingress-xxxxxxxxxx-xxxxxxxx.ap-northeast-1.elb.amazonaws.com   80      26m


# scaledjobリソースの一覧
$ kubectl get scaledjob -n kintaro-prd
NAME           MIN   MAX   TRIGGERS        AUTHENTICATION                      READY   ACTIVE   PAUSED    AGE
timecard-job               aws-sqs-queue   keda-trigger-auth-aws-credentials   True    True     Unknown   39s

# scaledjobリソースの詳細確認
$ kubectl describe scaledjob <scaled-object-name> -n kintaro-prd

# triggerauthenticationリソースの確認
$ kubectl get triggerauthentication -n kintaro-prd
NAME                                PODIDENTITY   SECRET   ENV   VAULTADDRESS
keda-trigger-auth-aws-credentials   aws

# triggerauthenticationリソースの詳細確認
$ kubectl describe triggerauthentication <trigger-authentication-name> -n kintaro-prd
```