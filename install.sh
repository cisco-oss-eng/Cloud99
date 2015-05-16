#!/bin/bash
echo "Cloud99 Setup"
echo "-------------"; echo

#setup_logs="/tmp/setup.log_"`date +"%b%d%y_%H%M%S"`
curdir=`pwd`
cur_root=${curdir%/*}
old_pythonpath=${PYTHONPATH}
pythonpath="${curdir}"


#echo "setup log: $setup_logs"; echo
#git_pull git@github.com:bdastur/rex.git ../rex

################################################
# Set the pythonpath.
################################################
export HAPATH=${pythonpath}
export PYTHONPATH=${pythonpath}

echo "================================================="
echo "New PYTHONPATH: '${PYTHONPATH}'"
echo "New HAPATH: '${PYTHONPATH}'"
echo "Old PYTHONPATH: '${old_pythonpath}'"
echo "================================================="
