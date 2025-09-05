#!/bin/bash
for fname in $(git diff --name-only); do
    if [[ ! -f "$fname" ]]; then
        echo "Skipping $fname (deleted or not a file)"
        continue
    fi
    if [[ $fname == *.py ]]
    then
        echo "Checking $fname with python linters"
        isort  --settings-path src/python --profile black "$fname"
        pylint "$fname" --rcfile standarts/pylintrc
        pyink -l 200 "$fname"
    fi
    if [[ $fname == *.yaml || $fname == *.yml ]]
    then
        echo "Checking $fname with yaml linters"
        yamllint "$fname"
    fi
    if [[ $fname == *.sh ]]
    then
        echo "Checking $fname with bash linter"
        bashlint "$fname"
    fi
    if [[ $fname == *.html || $fname == *.js ]]
    then
        echo "Checking $fname with prettier linters"
         prettier -w "$fname"
    fi
done
