export PROJECT_NAME="kintaro"

function error {
  echo "[error] $@" >&2
  exit 1
}
function info {
  echo "[info] $@" >&2
}
