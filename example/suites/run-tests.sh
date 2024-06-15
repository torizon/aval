#!/bin/bash

start=$(date +%s)

execute_tests() {
    local dir="$1"
    local formatter="$2"
    local test_files=$(find "$dir" -type f -name '*.bats')
    if [ -n "$test_files" ]; then
        for test_file in $test_files; do
            if [ "$formatter" = "junit" ]; then
                bats --report-formatter junit --output /home/torizon "$test_file"
            else
                bats "$test_file"
            fi
        done
    else
        echo "No test files found in $dir directory"
    fi
}

formatter=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -j|--junit) formatter="junit"; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

for dir in .; do
    if [ -d "meta/$dir" ]; then
        echo "Running tests in meta/$dir directory..."
        execute_tests "meta/$dir" "$formatter"
    else
        echo "Directory meta/$dir does not exist"
    fi
done

end=$(date +%s)
runtime=$((end-start))
echo "Total execution time: $runtime seconds"
