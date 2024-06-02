#!/bin/bash -l

function usage {
cat >&2 <<EOS
コンテナ起動コマンド

[usage]
 $0 <MODE> [options]

[args]
  MODE:
    job    : jobを起動
    shell  : コンテナにshellでログイン

[options]
 -h | --help:
   ヘルプを表示
 -e | --env <ENV_PATH>:
   環境変数ファイルのパスを指定 (default: ${ROOT_DIR}/app/local.env)
 -p | --prd:
    本番環境モードで起動
EOS
exit 1
}

ROOT_DIR="$(cd $(dirname $0)/..; pwd)"
source $ROOT_DIR/bin/lib/setting.sh

ENV_PATH="${ROOT_DIR}/app/env/local.env"
MODE=
BUILD=
args=()
while [ "$#" != 0 ]; do
  case $1 in
    -h | --help  ) usage;;
    -e | --env   ) shift; ENV_PATH=$1 ;;
    -b | --build ) BUILD="1" ;;
    -* | --*     ) echo "$1 : 不正なオプションです" >&2; exit 1 ;;
    *            ) args+=("$1") ;;
  esac
  shift
done

[ "${#args[@]}" != 1 ] && usage
MODE="${args[0]}"

if [[ ! "$MODE" =~ ^(shell|job|crawler|backend)$ ]]; then
  echo "--mode には shell, job, crawler, backend のいずれかを指定してください" >&2
  exit 1
fi

ENV_ABS_PATH=$(cd $(dirname $ENV_PATH); pwd)/$(basename $ENV_PATH)
if [ ! -f "$ENV_ABS_PATH" ]; then
  echo "$ENV_ABS_PATH が存在しません" >&2
  exit 1
fi

set -e
cd "$ROOT_DIR"

docker build \
  -f docker/app/Dockerfile \
  -t $PROJECT_NAME/app:latest \
  .


OPTIONS=
if [ "$MODE" = "shell" ]; then
  CMD="/bin/bash"
elif [ "$MODE" = "job" ]; then
  CMD="poetry run python job.py"
else
  CMD="/bin/bash"
fi

docker run --rm -ti \
  $OPTIONS \
  --network "br-kintaro" \
  --env-file "$ENV_ABS_PATH" \
  -e "DEBUG=1" \
  -v ${HOST_PROJECT_ROOT}/app:/opt/app \
  -v ${HOST_PROJECT_ROOT}/tmp:/opt/app/tmp \
  $PROJECT_NAME/app:latest \
  $CMD