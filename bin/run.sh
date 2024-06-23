#!/usr/bin/env bash
set -e
set -o pipefail

export PYTHONPATH="$(pwd)/src/melly:$PYTHONPATH"
echo 'PYTHONPATH is: '${PYTHONPATH}

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${unameOut}"
esac

if [ -f .env ]; then
  echo 'Loading environment variables from .env file'
  while IFS='=' read -r key value
  do
    # Remove leading and trailing whitespace from the key
    key=$(echo $key | xargs)
    # Use printf to handle multi-line and special character literals correctly
    value=$(echo "$value" | xargs)
    # Check if value starts with a double quote and ends with a double quote
    if [[ "$value" =~ ^\".*\"$ ]]; then
      # It's likely a JSON string, so preserve it
      eval export $key=$value
    else
      # Not a JSON string, so just export normally
      export $key="$value"
    fi
  done < .env
fi

if test "x${ENV}" = 'x'; then
  export ENV=dev
fi

echo 'Environment is: '${ENV}

if test "x${PORT}" = 'x'; then
  export PORT=8080
fi
if test "x${HOST}" = 'x'; then
  export HOST=0.0.0.0
fi

# Control number of workers for uvicorn
if test "x${WEB_CONCURRENCY}" = 'x'; then
  echo 'WEB_CONCURRENCY is not set, setting it to number of cores'
  if [ "$machine" == "Mac" ]; then
    export WEB_CONCURRENCY=1
  else
    export WEB_CONCURRENCY=`nproc --all`
  fi
fi
echo 'WEB_CONCURRENCY is: '${WEB_CONCURRENCY}

echo 'MONGO_URL is: '${MONGO_URL}

# Running the app
if test "x${ENV}" = 'xdev'; then
  if test "x${APPNAME}" = "xapi" ; then
    uvicorn melly.appmellyapi.web:app --host $HOST --port $PORT --log-level debug --reload --reload-dir src
  fi
else
  if test "x${APPNAME}" = "xapi" ; then
    uvicorn melly.appmellyapi.web:app --host $HOST --port $PORT --log-level info --proxy-headers --workers $WEB_CONCURRENCY
  fi
fi
