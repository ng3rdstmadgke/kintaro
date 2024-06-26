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
  # 取得コマンド: aws eks describe-cluster --name クラスタ名 --query "cluster.identity.oidc.issuer" --output text
  type = string
}

variable "vpc_id" {
  type = string
}

variable "app_namespace" {
  type = string
  default = "*"
}

variable "app_service_account" {
  type = string
  default = "*"
}

variable "jobcan_client_code" {
  type = string
}

variable "cognito_user_pool_id" {
  type = string
}

variable "cognito_client_id" {
  type = string
}

variable "kms_admin_list" {
  type = list(string)
  default = []
}
variable "keda_operator_role_arn" {
  type = string
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
output "app_role_arn" {
  value = aws_iam_role.timecard_job.arn
}
output "dynamodb_table_name" {
  value = aws_dynamodb_table.users.name
}
output "secret_name" {
  value = aws_secretsmanager_secret.app.name
}
output "app_alb_sg" {
  value = aws_security_group.app_alb.tags["Name"]
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
  name = "${local.app_name}-${local.stage}-users"
  billing_mode   = "PAY_PER_REQUEST"

  hash_key       = "username"
  //range_key      = "timestamp"

  attribute {
    name = "username"
    type = "S"
  }
}

/**
 * KMS
 *   - ジョブカンパスワード暗号化用
 */
# KMSキーの作成
resource "aws_kms_key" "this" {
  description = "${local.app_name}-${local.stage}"
  deletion_window_in_days = 10

  policy = jsonencode({
    "Version": "2012-10-17",
    "Id": "key-default-1",
    "Statement": [
      {
        "Sid": "Enable IAM User Permissions",
        "Effect": "Allow",
        "Principal": {
          "AWS": var.kms_admin_list
        },
        "Action": "kms:*",
        "Resource": "*"
      },
      {
        "Sid": "Allow use of the key",
        "Effect": "Allow",
        "Principal": {
          "AWS": [
            aws_iam_role.timecard_job.arn,
          ]
        },
        "Action": [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ],
        "Resource": "*"
      }
    ]
  })

  tags = {
    Name = "${local.app_name}-${local.stage}"
  }
}

/**
 * ALB のセキュリティグループ
 */
resource "aws_security_group" "app_alb" {
  name        = "${local.app_name}-${local.stage}-AppAlb"
  description = "Allow HTTP access."
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow HTTP access."
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "${local.app_name}-${local.stage}-AppAlb"
  }
}


/**
 * Cognito User Pool
 *   - ユーザー認証用
 */
data "aws_cognito_user_pool_client" "this" {
  client_id    = var.cognito_client_id
  user_pool_id = var.cognito_user_pool_id
}

/**
 * Random Password
 *   - トークン生成用の秘密鍵
 */
resource "random_password" "token_secret_key" {
  length           = 64
  min_upper        = 4
  min_lower        = 4
  min_numeric      = 4
  min_special      = 4
  special          = true
}

/**
 * SecretsManager 
 *   - アプリケーションの秘密情報を管理する
 */
resource "aws_secretsmanager_secret" "app" {
  name = "/${local.app_name}/${local.stage}/app"
  recovery_window_in_days = 0
  force_overwrite_replica_secret = true
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    jobcan_client_code=var.jobcan_client_code
    cognito_user_pool_id=var.cognito_user_pool_id
    cognito_client_id=data.aws_cognito_user_pool_client.this.client_id
    cognito_client_secret=data.aws_cognito_user_pool_client.this.client_secret
    kms_key_id = aws_kms_key.this.key_id
    token_secret_key = random_password.token_secret_key.result
  })
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
        AWS = var.keda_operator_role_arn
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
      {
        "Effect": "Allow",
        "Action": [
          "secretsmanager:GetSecretValue",
        ],
        "Resource": [
          aws_secretsmanager_secret.app.arn
        ]
      },
      {
        "Effect": "Allow",
        "Action": [
          "kms:Decrypt",
          "kms:Encrypt",
        ],
        "Resource": [
          aws_kms_key.this.arn
        ]
      },
      {
        "Effect": "Allow",
        "Action": [
          "dynamodb:*",
        ],
        "Resource": [
          aws_dynamodb_table.users.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "timecard_job" {
  role = aws_iam_role.timecard_job.name
  policy_arn = aws_iam_policy.timecard_job.arn
}
