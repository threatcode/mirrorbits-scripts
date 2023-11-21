#!/bin/bash

set -eu

if ! command -v gnuplot >/dev/null 2>&1; then
    echo "Please install gnuplot. Aborting." >&2
    exit 1
fi

if [ $# -lt 1 ]; then
    echo "Usage: $0 [analyze-json.data]" >&2
    exit 1
fi

if [ ! -e "$1" ]; then
    echo "ERROR: Can't find $1" >&2
    exit 1
fi

filename=$(basename ${1%.dat})
gnuplot -c plot-total.plg $1 $filename
gnuplot -c plot-selected-excluded.plg $1 $filename
