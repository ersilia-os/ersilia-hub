if [ "$VIRTUAL_ENV" = "" ]; then
    echo "\nActivating virtual env..."
    export VIRTUAL_ENV="$(pwd)/.venv"
    export PATH="$VIRTUAL_ENV/bin:$PATH"
fi

python3 ./run.py $1

export VIRTUAL_ENV=""

