#!/bin/bash

if [ "$#" -eq 0 ]; then
  PART="all"
elif [ "$#" -gt 0 ]; then
  PART="$1"
fi

if [ "$#" -eq 2 ]; then
  SUFFIX="_$2"
fi

PARTS=("part1" "FSM" "shr")
for p in ${PARTS[@]}; do
  if [ $PART = $p ] || [ $PART = "all" ]; then
    FILE="${p}${SUFFIX}.circ"
    echo "Copy $FILE to tests/"
    cp $FILE tests/${p}.circ
  fi
done

cd tests
python3 ./test.py ${PART}
cd ..
