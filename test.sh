#!/bin/bash
#
# Travis CI tests


# immediately exit if any command has a non-zero exit status
set -e

# display the active Python distribution version
printf '%s\n' "$(python --version)"

# package the project
python setup.py sdist

# install the project
python setup.py install

# test for basic functionality
pyspeedtest

# test simple command line arguments
for opt in -h --help --version; do
    pyspeedtest "$opt"
done

# test http connection debug levels
for level in 0 1 2 3 4 5; do
    pyspeedtest -d "$level" &>/dev/null
    pyspeedtest --debug="$level" &>/dev/null
done

# test various test modes
for mode in 1 2 4 7; do
    pyspeedtest -m "$mode"
    pyspeedtest --mode="$mode"
done

# use numerous test runs
for runs in 1 2 4 7; do
    pyspeedtest -r "$runs"
    pyspeedtest --runs="$runs"
done

# test multiple arguments at once
[[ $(pyspeedtest) == $(pyspeedtest --debug=0 --mode=7 --runs=2) ]]
