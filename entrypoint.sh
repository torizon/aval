#!/bin/bash

eval $(ssh-agent -s)
echo "$PRIVATE_KEY" | tr -d '\r' | ssh-add -
mkdir -p ~/.ssh
chmod 700 ~/.ssh
python /aval/main.py "$@"
