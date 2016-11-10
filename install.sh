#!/bin/bash
echo "Cloud99 Setup"
echo "-------------"; echo

cur_script=$(readlink -f "${BASH_SOURCE[0]}")
script_dir=$(dirname "${cur_script}")

#setup_logs="/tmp/setup.log_"`date +"%b%d%y_%H%M%S"`
old_pythonpath=${PYTHONPATH}
pythonpath="${script_dir}"


#echo "setup log: $setup_logs"; echo
#git_pull git@github.com:bdastur/rex.git ../rex

################################################
# Set the pythonpath.
################################################
export HAPATH=${PWD}
export PYTHONPATH=${pythonpath}

echo "================================================="
echo "New PYTHONPATH: '${PYTHONPATH}'"
echo "New HAPATH: '${HAPATH}'"
echo "Old PYTHONPATH: '${old_pythonpath}'"
echo "================================================="
