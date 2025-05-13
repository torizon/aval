#!/bin/bash

start=$(date +%s)

BASE_DIR=/suites

cd "$BASE_DIR" || { echo "Failed to change directory to $BASE_DIR"; exit 1; }
bats --report-formatter junit --output /home/torizon --recursive .

echo "Executed bats command in $BASE_DIR"

end=$(date +%s)
runtime=$((end-start))
echo "Total execution time: $runtime seconds"
