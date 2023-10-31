#!/bin/bash

set -eu

if ! command -v gnuplot >/dev/null 2>&1; then
    echo "Please install gnuplot. Aborting." >&2
    exit 1
fi

filename=$(basename ${1%.dat})
gnuplot -c plot-total.plg $1 $filename
gnuplot -c plot-selected-excluded.plg $1 $filename
