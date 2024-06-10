variable "oidc_provider" {
  # 取得コマンド: aws eks describe-cluster --name eks-work-prd --query "cluster.identity.oidc.issuer" --output text
  type = string
}

variable "keda_namespace" {
  type = string
  default = "keda"
}

variable "app_namespace" {
  type = string
  default = "*"
}

variable "app_service_account" {
  type = string
  default = "*"
}
