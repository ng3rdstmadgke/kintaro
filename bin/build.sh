#!/bin/bash -l

function usage {
cat >&2 <<EOS
[usage]
 $0 [options]

[options]
 -h | --help:
   ヘルプを表示
 --push <STAGE>:
   同時に指定したステージにプッシュを行う
   <STAGE>: pushするステージ名を指定(stg, prd, など)
 --no-cache:
   キャッシュを使わないでビルド

[example]
 ビルドのみを実行する場合
 $0

 本番環境のイメージをpushする場合
 $0 --push prd --no-cache
EOS
exit 1
}

ROOT_DIR="$(cd $(dirname $0)/..; pwd)"
source $ROOT_DIR/bin/lib/setting.sh
cd "$ROOT_DIR"

AWS_REGION="ap-northeast-1"
PUSH_STAGE=
BUILD_OPTIONS="--rm"
args=()
while [ "$#" != 0 ]; do
  case $1 in
    -h | --help  ) usage;;
    --push       ) shift; PUSH_STAGE=$1 ;;
    --no-cache   ) BUILD_OPTIONS="$BUILD_OPTIONS --no-cache" ;;
    -* | --*     ) error "$1 : 不正なオプションです" ;;
    *            ) args+=("$1") ;;
  esac
  shift
done

[ "${#args[@]}" != 0 ] && usage

set -e
trap 'echo "[$BASH_SOURCE:$LINENO] - "$BASH_COMMAND" returns not zero status"' ERR

cd "$ROOT_DIR"

# AWSアカウントIDの取得
AWS_ACCOUNT_ID=$(aws $AWS_PROFILE_OPTION sts get-caller-identity --query 'Account' --output text)
info "AWS_ACCOUNT_ID: $AWS_ACCOUNT_ID"

#############################
# イメージのbuild
#############################
REMOTE_IMAGE_PREFIX="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}/${PUSH_STAGE:-local}"
VERSION=$(date +"%Y%m%d.%H%M")

# app
docker build $BUILD_OPTIONS \
  -f docker/app/Dockerfile \
  -t $PROJECT_NAME/app:latest \
  -t $REMOTE_IMAGE_PREFIX/app:latest \
  -t $REMOTE_IMAGE_PREFIX/app:$VERSION \
  .

# ビルドのみの場合はここで終了
[ -z "$PUSH_STAGE" ] && exit 0

#############################
# イメージのpush
#############################
# ECRログイン
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# push
docker push ${REMOTE_IMAGE_PREFIX}/app:latest
docker push ${REMOTE_IMAGE_PREFIX}/app:${VERSION}

info "イメージのプッシュが完了しました。"
info "IMAGE_URI: ${REMOTE_IMAGE_PREFIX}/app:${VERSION} (latest)"
