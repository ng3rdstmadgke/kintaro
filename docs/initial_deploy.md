# ■ update-kubeconfig

```bash
aws eks --region ap-northeast-1 update-kubeconfig --name eks-work-prd
```

# ■ terraformデプロイ

```bash
cd ${CONTAINER_PROJECT_ROOT}/terraform/env/prd
```

設定ファイルの編集

```bash
# OIDC Providerの取得
aws eks describe-cluster --name eks-work-prd --query "cluster.identity.oidc.issuer" --output text

# oidc_provider変数を定義
cp secrets.auto.tfvars.sample secrets.auto.tfvars
vim secrets.auto.tfvars
```

```bash
terraform init
terraform plan
terraform apply -auto-approve
```

# ■ dockerイメージのpush

```bash
cd $CONTAINER_PROJECT_ROOT
${CONTAINER_PROJECT_ROOT}/bin/build.sh --push prd
```


# ■ KEDA インストール

```bash
# リポジトリ追加・アップデート
helm repo add kedacore https://kedacore.github.io/charts
helm repo update

# kedaインストール
KEDA_OPERATOR_ROLE=$(cd ${CONTAINER_PROJECT_ROOT}/terraform/env/prd; terraform output -raw keda_operator_role_arn)
helm install keda kedacore/keda \
  --set podIdentity.aws.irsa.enabled=true \
  --set podIdentity.aws.irsa.roleArn=$KEDA_OPERATOR_ROLE \
  --namespace="keda" \
  --create-namespace
```

# ■ Kubenetesリソースのデプロイ

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

# ■ 動作確認

## Web

ブラウザで `http://k8s-producti-ingress-xxxxxxxxxx-xxxxxxxx.ap-northeast-1.elb.amazonaws.com` にアクセス

## crawler

なし

## バッチジョブ
```bash
cd $CONTAINER_PROJECT_ROOT

# 主要なリソースの監視
watch -n1 kubectl get all -n kintaro-prd

# sqsにメッセージを投げ込む
./bin/send-queue.sh <DynamoDBに登録してあるユーザー名>

# ログ確認
kubectl logs <pod_name> -n kintaro-prd
```

# ■ 削除

```bash
kubectl delete -k ${CONTAINER_PROJECT_ROOT}/kustomize/overlays/prd/

cd ${CONTAINER_PROJECT_ROOT}/terraform/env/prd
terraform destroy -auto-approve
```
