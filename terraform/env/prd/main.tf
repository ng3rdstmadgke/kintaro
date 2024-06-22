terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.8.0"

  backend "s3" {
    bucket = "tfstate-store-a5gnpkub"
    region = "ap-northeast-1"
    key = "kintaro/prd/terraform.tfstate"
    encrypt = true
  }
}

provider "aws" {
  region = "ap-northeast-1"
  default_tags {
    tags = {
      PROJECT_NAME = "KINTARO"
    }
  }
}

data "aws_caller_identity" "self" { }
data "aws_region" "self" {}

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

output "app_ecr_repository" {
  value = aws_ecr_repository.app.repository_url
}
output "app_sqs_url" {
  value = aws_sqs_queue.timecard_job_queue.url
}
output "keda_trigger_auth_role_arn" {
  value = aws_iam_role.keda_trigger_auth.arn
}
output "keda_operator_role_arn" {
  value = aws_iam_role.keda_operator.arn
}
output "app_role_arn" {
  value = aws_iam_role.timecard_job.arn
}

locals {
  app_name = "kintaro"
  stage = "prd"
  account_id = data.aws_caller_identity.self.account_id
  aws_region = data.aws_region.self.name
}

/**
 * ECR リポジトリ
 */
resource "aws_ecr_repository" "app" {
  name                 = "${local.app_name}/${local.stage}/app"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

/**
 * SQS (Pipeソース)
 * https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue.html
 */
resource "aws_sqs_queue" "timecard_job_queue" {
  name = "${local.app_name}-${local.stage}-TimecardJobQueue"
  # キューに送信されたメッセージがコンシューマに表示されるまでの時間 (秒)
  delay_seconds = 0
  # 最大メッセージサイズ (バイト)
  max_message_size = 262144 # 256KiB
  # メッセージ保持期間 (秒)
  message_retention_seconds = 604800 # 7 days
  # メッセージ受信待機時間 (秒)
  receive_wait_time_seconds = 0
  # 可視性タイムアウト (秒)
  # コンシューマがこの期間内にメッセージを処理して削除できなかった場合、メッセージは再度キューに表示される。
  visibility_timeout_seconds = 30
}

/**
 * DynamoDB
 * https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table
 */

resource "aws_dynamodb_table" "users" {
  name = "${local.app_name}-${local.stage}-Users"
  billing_mode   = "PAY_PER_REQUEST"

  hash_key       = "username"
  //range_key      = "timestamp"

  attribute {
    name = "username"
    type = "S"
  }
}


/**
 * KEDAがtriggerとして利用するSQSにアクセスするためのIAM Role  (このRoleはKubernetesのServiceAccountと紐づく)
 */
resource "aws_iam_role" "keda_trigger_auth" {
  name = "${local.app_name}-${local.stage}-KedaTriggerAuthRole"
  assume_role_policy = jsonencode({
    "Version": "2012-10-17"
    "Statement": {
      "Effect": "Allow",
      "Principal": {
        AWS = aws_iam_role.keda_operator.arn
      },
      "Action": "sts:AssumeRole",
    }
  })
}

resource "aws_iam_policy" "keda_trigger_auth" {
  name = "${local.app_name}-${local.stage}-KedaTriggerAuthPolicy"
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "sqs:GetQueueAttributes",
          "sqs:*",
        ],
        "Resource": [
          aws_sqs_queue.timecard_job_queue.arn
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "keda_trigger_auth" {
  role = aws_iam_role.keda_trigger_auth.name
  policy_arn = aws_iam_policy.keda_trigger_auth.arn
}

/**
 * KEDA Operator が利用するIAM Role
 * KedaTriggerAuthRole へのAssumeRole権限を持つ
 */
resource "aws_iam_role" "keda_operator" {
  name = "${local.app_name}-${local.stage}-KedaOperatorRole"
  assume_role_policy = jsonencode({
    "Version": "2012-10-17"
    "Statement": {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${local.account_id}:oidc-provider/${var.oidc_provider}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${var.oidc_provider}:sub": "system:serviceaccount:${var.keda_namespace}:keda-operator",
          "${var.oidc_provider}:aud": "sts.amazonaws.com"
        }
      }
    }
  })
}

resource "aws_iam_policy" "keda_operator" {
  name = "${local.app_name}-${local.stage}-KedaOperatorPolicy"
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "sts:AssumeRole",
        ],
        "Resource": [
          aws_iam_role.keda_trigger_auth.arn
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "keda_operator" {
  role = aws_iam_role.keda_operator.name
  policy_arn = aws_iam_policy.keda_operator.arn
}


/**
 * アプリケーション用のIAM Role  (このRoleはKubernetesのServiceAccountと紐づく)
 */
resource "aws_iam_role" "timecard_job" {
  name = "${local.app_name}-${local.stage}-TimecardJobRole"
  assume_role_policy = jsonencode({
    "Version": "2012-10-17"
    "Statement": {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${local.account_id}:oidc-provider/${var.oidc_provider}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringLike": {
          "${var.oidc_provider}:sub": "system:serviceaccount:${var.app_namespace}:${var.app_service_account}",
          "${var.oidc_provider}:aud": "sts.amazonaws.com"
        }
      }
    }
  })
}

resource "aws_iam_policy" "timecard_job" {
  name = "${local.app_name}-${local.stage}-TimecardJobPolicy"
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:*",
          "s3-object-lambda:*"
        ],
        "Resource": [
          "*"
        ]
      },
      {
        "Effect": "Allow",
        "Action": [
          "sqs:*",
        ],
        "Resource": [
          aws_sqs_queue.timecard_job_queue.arn
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "timecard_job" {
  role = aws_iam_role.timecard_job.name
  policy_arn = aws_iam_policy.timecard_job.arn
}
