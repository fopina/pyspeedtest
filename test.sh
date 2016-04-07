#!/bin/bash
#
# Travis CI tests


# immediately exit if any command has a non-zero exit status
set -e

# enable xtrace
set -x

# package the project
python setup.py sdist

# install the project
python setup.py install

# test for basic functionality
pyspeedtest

# test simple command line arguments
for arg in -h --help --version; do
    pyspeedtest "$arg"
done

# test http connection debug levels
for level in 0 1 2 3 4 5; do
    pyspeedtest -d "$level" &>/dev/null
    pyspeedtest --debug "$level" &>/dev/null
    pyspeedtest --debug="$level" &>/dev/null
done

# test various test modes
for mode in 1 2 4 7; do
    pyspeedtest -m "$mode"
    pyspeedtest --mode "$mode"
    pyspeedtest --mode="$mode"
done

# use numerous test runs
for runs in 1 2 4 7; do
    pyspeedtest -r "$runs"
    pyspeedtest --runs "$runs"
    pyspeedtest --runs="$runs"
done

# use different output formats
for format in default json xml; do
	pyspeedtest -f "$format"
	pyspeedtest --format "$format"
	pyspeedtest --format="$format"
done

# test multiple arguments at once and verify output
pyspeedtest --debug=0 --mode=7 --runs=2 |& grep -qE $'^Using server: .*\nPing: [0-9]+ ms\nDownload speed: [0-9.]+ (bps|Kbps|Mbps|Gbps)\nUpload speed: [0-9.]+ (bps|Kbps|Mbps|Gbps)$'

# test for bad arguments
! pyspeedtest -x
! pyspeedtest --xxx

# test for bad debug levels
for arg in -d --debug; do
    ! output=$(pyspeedtest "${arg}" xxx 2>&1)
    [[ $output = "usage: pyspeedtest [OPTION]...
pyspeedtest: error: argument -d/--debug: invalid positive int value: 'xxx'" ]]
done

# test for bad modes
for badmode in -1 0 8 9 10 11 12 13 14 15; do
    for arg in -m --mode; do
        ! output=$(pyspeedtest "${arg}" "${badmode}" 2>&1)
        [[ $output = "usage: pyspeedtest [OPTION]...
pyspeedtest: error: argument -m/--mode: invalid choice: ${badmode} (choose from 1, 2, 3, 4, 5, 6, 7)" ]]
    done
done

# test for bad runs
for arg in -r --runs; do
    ! output=$(pyspeedtest "${arg}" xxx 2>&1)
    [[ $output = "usage: pyspeedtest [OPTION]...
pyspeedtest: error: argument -r/--runs: invalid positive int value: 'xxx'" ]]
done

# test for bad output formats
for arg in -f --format; do
	! output=$(pyspeedtest "${arg}" xxx 2>&1)
	[[ $output = "usage: pyspeedtest [OPTION]...
pyspeedtest: error: argument -f/--format: output format not supported: 'xxx'" ]]
done
