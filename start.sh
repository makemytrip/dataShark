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

# LOAD ENVIRONMENT
source datashark-env.sh

## FLAG CHECKS
while [[ $# -gt 0 ]]
do
	key="$1"

	case $key in
		-l|--local)
			LOCAL="--local"
			SPARK_INSTANCE="local[*]"
			shift
		;;

		*)	# unknown option
			;;
	esac
	shift 
done

echo '                                                            '
echo '               __      __        _____ __               __  '
echo '          ____/ /___ _/ /_____ _/ ___// /_  ____ ______/ /__'
echo '         / __  / __ `/ __/ __ `/\__ \/ __ \/ __ `/ ___/ //_/'
echo '        / /_/ / /_/ / /_/ /_/ /___/ / / / / /_/ / /  / ,<   '
echo '        \__,_/\__,_/\__/\__,_//____/_/ /_/\__,_/_/  /_/|_|  '
echo '                                                            '
echo '                          PRODUCTION MODE                   '
echo '                                                            '
echo '                               v1.1                         '
echo '                                                            '
echo '                                                            '

if [ -z "$LOCAL" ]; then
	echo "$INFO $(date '+%Y-%m-%d %H:%M:%S') Running Spark on Cluster"
else
	echo "$INFO $(date '+%Y-%m-%d %H:%M:%S') Running Spark on Local Machine"
fi

FILES=`ls conf/*/* | grep -v .pyc | grep -v __init__ | awk -vORS=, '{ print $1 }' | sed 's/,$/\n/'`
COPY_TO_HDFS=`ls conf/*/* | grep -v .pyc | grep -v __init__ | awk -vORS=' ' '{ print $1 }' | sed 's/ $/\n/'`

echo "$INFO $(date '+%Y-%m-%d %H:%M:%S') Preparing FileSystem"
hdfs dfs -rm -r /user/root/driverFiles
hdfs dfs -mkdir /user/root/driverFiles
hdfs dfs -put $COPY_TO_HDFS /user/root/driverFiles

echo "$INFO $(date '+%Y-%m-%d %H:%M:%S') Starting Spark"

JARS=`ls lib/*.jar | awk -vORS=, '{ print $1 }' | sed 's/,$/\n/'`
PLUGINS=`find plugins | grep ".py$" | grep -v __init__`
cp -f $PLUGINS .
CLEANUP=`for i in $PLUGINS; do basename $i; done | awk -vORS=' ' '{ print $1"*" }' | sed 's/ $/\n/'`
PLUGINS=`echo $PLUGINS  | sed 's/ /,/g'`

spark-submit --jars $JARS --master $SPARK_INSTANCE --files=$FILES,$PLUGINS --driver-java-options="-Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=0 -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:ParallelGCThreads=10" --conf spark.executor.extraJavaOptions="-Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=0 -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:ParallelGCThreads=10" --executor-memory 4G --driver-memory 2G datashark.py $LOCAL

echo "$INFO $(date '+%Y-%m-%d %H:%M:%S') Cleaning Up"
rm -f $CLEANUP
hdfs dfs -rm -r /user/root/driverFiles >> hdfs.log 2>&1
