#!/bin/bash -l

function usage {
cat >&2 <<EOS
コンテナ起動コマンド

[usage]
 $0 <MODE> [options]

[args]
  MODE:
    job <USERNAME>:
      jobを起動
    app:
      webアプリコンテナを起動
    crawler:
      crawlerを起動
    shell:
      コンテナにshellでログイン

[options]
 -h | --help:
   ヘルプを表示
 -e | --env <ENV_PATH>:
   環境変数ファイルのパスを指定 (default: ${CONTAINER_PROJECT_ROOT}/.env)
EOS
exit 1
}

source $CONTAINER_PROJECT_ROOT/bin/lib/setting.sh

ENV_PATH="${CONTAINER_PROJECT_ROOT}/.env"
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

[ "${#args[@]}" -lt 1 ] && usage
MODE="${args[0]}"
USERNAME="${args[1]}"

if [[ ! "$MODE" =~ ^(shell|job|crawler|app)$ ]]; then
  echo "--mode には shell, job, crawler, app のいずれかを指定してください" >&2
  exit 1
fi

if [ "$MODE" = "job" ] && [ -z "$USERNAME" ]; then
  echo "job モードの場合は USERNAME を指定してください" >&2
  exit 1
fi

ENV_ABS_PATH=$(cd $(dirname $ENV_PATH); pwd)/$(basename $ENV_PATH)
if [ ! -f "$ENV_ABS_PATH" ]; then
  echo "$ENV_ABS_PATH が存在しません" >&2
  exit 1
fi

set -e
cd "$CONTAINER_PROJECT_ROOT"

docker build \
  -f docker/app/Dockerfile \
  -t $PROJECT_NAME/app:latest \
  .

OPTIONS=
if [ "$MODE" = "shell" ]; then
  CMD="/bin/bash"
elif [ "$MODE" = "job" ]; then
  CMD="poetry run python job.py $USERNAME"
elif [ "$MODE" = "app" ]; then
  CMD="poetry run uvicorn app:app --workers 2 --host 0.0.0.0 --port 8080 --reload"
  OPTIONS="$OPTIONS -p 8080:8080 --name ${PROJECT_NAME}-app"
elif [ "$MODE" = "crawler" ]; then
  CMD="poetry run python crawler.py"
else
  echo "不正なモードです" >&2
  exit 1
fi

# docker network
NETWORK_NAME="br-kintaro"
NETWORK_EXISTS="$(docker network inspect $NETWORK_NAME >/dev/null 2>&1; echo $?)"
if [ "$NETWORK_EXISTS" = 1 ]; then
  docker network create --driver bridge --subnet "$NETWORK_CIDR" $NETWORK_NAME
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