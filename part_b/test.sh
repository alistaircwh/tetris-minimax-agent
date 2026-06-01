#!/bin/bash

output_file="testing/agent_test.txt"

for i in {1..100}
do
    echo "GAME ${i}: $(python -m referee agent agent_random -v 0)" | tee -a "$output_file"
    echo "GAME ${i}: $(python -m referee agent_random agent -v 0)" | tee -a "$output_file"
done