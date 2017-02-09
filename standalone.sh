#!/bin/bash
#
# Copyright 2016 MakeMyTrip (Kunal Aggarwal)
#
# This file is part of dataShark.
#
# dataShark is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# dataShark is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with dataShark.  If not, see <http://www.gnu.org/licenses/>.

## GLOBALS
ERROR="[X]"
WARN="[!]"
INFO="[*]"

JARS=`ls lib/*.jar | awk -vORS=, '{ print $1 }' | sed 's/,$/\n/'`
CDIR=`pwd`
CODE_PATH=`ls conf/ | grep -v ".py" | xargs -i echo "$CDIR/conf/{}" | awk -vORS=: '{ print $1 }' | sed 's/:$/\n/'`

# LOAD ENVIRONMENT
source datashark-env.sh

DEBUG=""

while getopts ":d:" opt; do
  case $opt in
    d)
      DEBUG="debug"
      CODEFILE=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

export PYTHONPATH=$SPARK_HOME/python:$CODE_PATH:$CDIR/plugins/output:$PYTHONPATH

echo '                                                            '
echo '               __      __        _____ __               __  '
echo '          ____/ /___ _/ /_____ _/ ___// /_  ____ ______/ /__'
echo '         / __  / __ `/ __/ __ `/\__ \/ __ \/ __ `/ ___/ //_/'
echo '        / /_/ / /_/ / /_/ /_/ /___/ / / / / /_/ / /  / ,<   '
echo '        \__,_/\__,_/\__/\__,_//____/_/ /_/\__,_/_/  /_/|_|  '
echo '                                                            '
echo '                          STANDALONE MODE                   '
echo '                                                            '
echo '                               v1.2                         '
echo '                                                            '
echo '                                                            '
      
if [ "x$DEBUG" == "x" ]; then
	CODEFILE=$1
else	
	echo "$INFO Debug Mode is ON" >&2
fi

spark-submit --jars $JARS --master local[*] --executor-memory 4G --driver-memory 2G datashark_standalone.py $CODEFILE $DEBUG
