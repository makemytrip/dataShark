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

## SCRIPT VARIABLES
RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
NC='\033[0m'
INFO="[${GREEN}INFO${NC}]"
WARN="[${ORANGE}WARN${NC}]"
ERROR="[${RED}ERROR${NC}]"

## Check if script is run as root
if [ "$EUID" -ne 0 ]
  then echo -e "Please run this script as root"
  exit 1
fi

## Get the install prefix. Default is /etc
INSTALL_PREFIX="/etc"
for i in "$@"
do
	case $i in
	    --prefix=*)
	    	INSTALL_PREFIX="${i#*=}"
	    	shift
	    ;;
	    *)
		# unknown option
	    ;;
	esac
done
if [ "x$INSTALL_PREFIX" == "x" ]; then
	INSTALL_PREFIX="/etc"
fi

BRANCH_NAME="master"
DATASHARK_GIT_REPO="https://github.com/makemytrip/dataShark.git"
BASE_DIR="$INSTALL_PREFIX/datashark"
TMP_DIR="/tmp"
INIT_DIR=/etc/init.d/

banner() {
	echo '             __      __        _____ __               __  '
	echo '        ____/ /___ _/ /_____ _/ ___// /_  ____ ______/ /__'
	echo '       / __  / __ `/ __/ __ `/\__ \/ __ \/ __ `/ ___/ //_/'
	echo '      / /_/ / /_/ / /_/ /_/ /___/ / / / / /_/ / /  / ,<   '
	echo '      \__,_/\__,_/\__/\__,_//____/_/ /_/\__,_/_/  /_/|_|  '
	echo '                                                          '
	echo '                            INSTALLER                     '
	echo '                                                          '
	echo '                                                          '
}
banner

## Detect System type, Ubuntu or CentOS
SYSTEM_TYPE="`python -mplatform | grep -i Ubuntu`"
if [ "x$SYSTEM_TYPE" != "x" ]; then
	DISTRO="UBUNTU"
	BASHRC_FILE="/etc/bash.bashrc"
else
	DISTRO="CENTOS"
	BASHRC_FILE="/etc/bashrc"
fi

## Create the dataShark Directory
mkdir -p $BASE_DIR/install

echo -e "" >> $BASHRC_FILE
echo -e "" >> $BASHRC_FILE
echo -e "## ENVIRONMENT VARIABLES SET BY DATASHARK" >> $BASHRC_FILE
echo -e "export DATASHARK_HOME=$BASE_DIR" >> $BASHRC_FILE

## Check Installed Scala and its version
check_installed_scala() {
	echo -e "$INFO Checking for installed Scala"
	where_scala="`type -p scala`"
	if [ "x$where_scala" != "x" ]; then
		echo -e "$INFO Found Scala in PATH -> $where_scala"
		_scala=scala
	else
		echo -e "$ERROR No Scala Installation Found"
		return 3
	fi

	if [[ "$_scala" ]]; then
		version=$("$_scala" -version 2>&1 | awk '{print $5}')	
		if [[ "$version" > "2.11.7" ]]; then
			echo -e "$INFO Scala version is greater than 2.11.7 -> $version"
			return 0
		else
			echo -e "$ERROR Scala version is less than 2.11.8 -> $version"	
			return 1
		fi
	fi
}

## Check Installed Java and its version
check_installed_java() {
	echo -e "$INFO Checking for installed Java"
	where_java="`type -p java`"
	if [ "x$where_java" != "x" ]; then
		echo -e "$INFO Found java executable in PATH -> $where_java"
		_java=java
	elif [[ -n "$JAVA_HOME" ]] && [[ -x "$JAVA_HOME/bin/java" ]];  then
		echo -e "$INFO Found java executable in JAVA_HOME"     
		_java="$JAVA_HOME/bin/java"
	else
		echo -e "$ERROR No java installation found"
		return 3
	fi

	if [[ "$_java" ]]; then
		version=$("$_java" -version 2>&1 | awk -F '"' '/version/ {print $2}')
		if [[ "$version" > "1.8" ]]; then
			echo -e "$INFO Java version is more than 1.8 -> $version"
			return 0
		else         
			echo -e "$WARN Java version is less than 1.8 -> $version"
			return 1
		fi
	fi	
}

## Check Installed Git and GCC
check_and_install_git() {
	where_git="`type -p git`"
	if [ "x$where_git" != "x" ]; then
		echo -e "$INFO Found git installed. Checking for gcc."
		where_gcc="`type -p gcc`"
		if [ "x$where_gcc" != "x" ]; then
			echo -e "$INFO Found gcc installed. Skipping..."
			return 0
		else
			python -mplatform | grep -i Ubuntu && apt-get -y install gcc || yum -y install gcc
		fi
	else
		python -mplatform | grep -i Ubuntu && apt-get -y install git gcc || yum -y install git gcc
	fi
}

## Check Installed Spark and its version
check_installed_spark() {
	echo -e "$INFO Checking for installed Spark"
	where_spark="`type -p spark-submit`"
	if [ "x$where_spark" != "x" ]; then
		echo -e "$INFO Found Spark Executables in PATH -> $where_spark"
		_spark_submit=spark-submit
	else
		echo -e "$ERROR No Spark Installation Found"
		return 3
	fi

	if [[ "$_spark_submit" ]]; then
		version=$("$_spark_submit" --version 2>&1 | grep version | awk '{print $NF}')
		if [[ "$version" > "1.6.1" ]]; then
			echo -e "$INFO Spark version is more than 1.6.1 -> $version"
			return 0
		else
			echo -e "$WARN Spark version is less than 1.6.2 -> $version"
                        return 1
		fi
	fi
}

## Install Python Dependencies
install_python_deps() {
	echo -e "$INFO Installing Python Dependencies"
	python -mplatform | grep -i Ubuntu && apt-get -y install python-setuptools python-dev || yum -y install python-setuptools python-devel
	check_pip="`type -p pip`"
	if [ "x$check_pip" != "x" ]; then
		pip install py4j configobj argparse numpy
	else
		easy_install py4j configobj argparse numpy
	fi
	echo -e "$INFO Python Dependencies installed"
}

## Install Scala Version 2.11.8
install_scala() {
	echo -e "$INFO Downloading Scala"
	wget -O $BASE_DIR/install/scala.tgz http://downloads.lightbend.com/scala/2.11.8/scala-2.11.8.tgz 1> /dev/null 2> /dev/null
	echo -e "$INFO Unpacking Scala"
	tar -xf $BASE_DIR/install/scala.tgz -C $BASE_DIR
	mv $BASE_DIR/scala* $BASE_DIR/scala
	echo -e "$INFO Installing Scala to environment"
	echo -e "export PATH=\$PATH:$BASE_DIR/scala/bin" >> $BASHRC_FILE
	export PATH=$PATH:$BASE_DIR/scala/bin
	echo -e "$INFO Installed Scala Successfully"
}

## Install Java 8u112
install_java() {
	MACHINE_TYPE=`uname -m`
	if [ ${MACHINE_TYPE} == 'x86_64' ]; then
		echo -e "$INFO System is 64 bit"
		echo -e "$INFO Downloading Java"
		wget -O $BASE_DIR/install/java.tar.gz --no-cookies --no-check-certificate --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/8u112-b15/jdk-8u112-linux-x64.tar.gz 1> /dev/null 2> /dev/null
	else
		echo -e "$INFO System is 32 bit"
		echo -e "$INFO Downloading Java"
		wget -O $BASE_DIR/install/java.tar.gz --no-cookies --no-check-certificate --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/8u112-b15/jdk-8u112-linux-i586.tar.gz 1> /dev/null 2> /dev/null	
	fi
	echo -e "$INFO Unpacking Java"
	tar -xf $BASE_DIR/install/java.tar.gz -C $BASE_DIR
	mv $BASE_DIR/jdk* $BASE_DIR/java
	echo -e "$INFO Installing Java to environment"
	if [ "$DISTRO" == "UBUNTU" ]; then
		update-alternatives --install /usr/bin/java java $BASE_DIR/java/bin/java 2
	        update-alternatives --install /usr/bin/jar jar $BASE_DIR/java/bin/jar 2
	        update-alternatives --install /usr/bin/javac javac $BASE_DIR/java/bin/javac 2
	        update-alternatives --set java $BASE_DIR/java/bin/java
	        update-alternatives --set jar $BASE_DIR/java/bin/jar
	        update-alternatives --set javac $BASE_DIR/java/bin/javac
	else
		alternatives --install /usr/bin/java java $BASE_DIR/java/bin/java 2
	        alternatives --install /usr/bin/jar jar $BASE_DIR/java/bin/jar 2
        	alternatives --install /usr/bin/javac javac $BASE_DIR/java/bin/javac 2
	        alternatives --set java $BASE_DIR/java/bin/java
        	alternatives --set jar $BASE_DIR/java/bin/jar
	        alternatives --set javac $BASE_DIR/java/bin/javac
	fi

	echo -e "export JAVA_HOME=$BASE_DIR/java" >> $BASHRC_FILE
	echo -e "export JRE_HOME=$BASE_DIR/java/jre" >> $BASHRC_FILE
	echo -e "export PATH=\$PATH:$BASE_DIR/java/bin:$BASE_DIR/java/jre/bin" >> $BASHRC_FILE
	export JAVA_HOME=$BASE_DIR/java
	export JRE_HOME=$BASE_DIR/java/jre
	export PATH=$PATH:$BASE_DIR/java/bin:$BASE_DIR/java/jre/bin
	
	echo -e "$INFO Installed Java Successfully"
}

## Install Spark 1.6.2
install_spark() {
	echo -e "$INFO Downloading Spark"
	wget -O $BASE_DIR/install/spark.tgz http://d3kbcqa49mib13.cloudfront.net/spark-1.6.2.tgz 1> /dev/null 2> /dev/null 
	echo -e "$INFO Extracting Spark"
	tar -xf $BASE_DIR/install/spark.tgz -C $BASE_DIR
	mv $BASE_DIR/spark* $BASE_DIR/spark
	cd $BASE_DIR/spark
	echo -e "$INFO Compiling Spark (This will take a lot of time ~20-30 mins, go grab a cup of coffee)"
	sbt/sbt assembly
	cp -f conf/log4j.properties.template conf/log4j.properties
	sed -i "s/log4j.rootCategory=INFO, console/log4j.rootCategory=ERROR, console/g" conf/log4j.properties
	echo -e "$INFO Testing Spark"
	echo "127.0.0.1 `hostname` #Added by dataShark" >> /etc/hosts
	lines=`./bin/run-example SparkPi 10 2>&1 | wc -l`
	if [ $lines -eq 1 ]; then 
		echo -e "$INFO Spark compiled successfully"
		echo -e "$INFO Setting up Spark in environment"
		echo -e "export PATH=\$PATH:$BASE_DIR/spark/bin" >> $BASHRC_FILE
		echo -e "export SPARK_HOME=$BASE_DIR/spark" >> $BASHRC_FILE
		echo -e "export PYTHONPATH=\$SPARK_HOME/python:\$PYTHONPATH" >> $BASHRC_FILE
		export PATH=$PATH:$BASE_DIR/spark/bin
		export SPARK_HOME=$BASE_DIR/spark
		export PYTHONPATH=$SPARK_HOME/python:$PYTHONPATH
	
	else
		echo -e "$ERROR There was some issue in spark compilation, please refer http://spark.apache.org/docs/1.6.2/ for more info."
	fi
}

## Install dataShark
install_datashark() {
	echo -e "$INFO Downloading dataShark"
	cd $BASE_DIR
	git init
	git remote add origin $DATASHARK_GIT_REPO
	git fetch
	git checkout -t origin/$BRANCH_NAME
	echo -e "$INFO dataShark has been setup successfully in $BASE_DIR"
	echo -e "$INFO Please execute 'source $BASHRC_FILE' before running dataShark. Please note, this is one time only."
}


## MAIN SCRIPT

check_installed_java
retval=$?
if [ $retval -eq 0 ]; then
	echo -e "$INFO Java is already installed"
elif [ $retval -eq 3 ]; then
	echo -e "$INFO I couldn't locate Java on your system. I'll install it now!"
	install_java
else
	ji="q"
	echo -e "$INFO I recommend Java 1.8.0 to be installed on your system. Your existing installation didn't meet the required criteria."
	while [ "x$ji" != "x" ]; do
		read -p $'[\e[33mWARN\e[0m] Shall I (c)ontinue with the existing Java installation or (i)nstall Java 1.8.0. [c/i]: ' ji
		case $ji in
	       		[iI]* ) install_java; break;;
	        	[cC]* ) break;;
		        * ) ji="q";;
		esac
	done
fi

check_installed_scala
retval=$?
if [ $retval -eq 0 ]; then
	echo -e "$INFO Scala is already installed"
elif [ $retval -eq 3 ]; then
	echo -e "$WARN I couldn't locate Scala on your system. I'll install it now!"
	install_scala
else
	si="q"
	echo -e "$INFO I recommend Scala 2.11.8 to be installed on your system. Your existing installation didn't meet the required criteria."
	while [ "x$si" != "x" ]; do
		read -p $'[\e[33mWARN\e[0m] Shall I (c)ontinue with the existing Scala installation or (i)nstall Scala 2.11.8. [c/i]: ' si
		case $si in
                	[iI]* ) install_scala; break;;
                        [cC]* ) break;;
                        * ) si="q";;
        	esac
	done
fi

check_and_install_git
install_python_deps

check_installed_spark
retval=$?
if [ $retval -eq 0 ]; then
	echo -e "$INFO Spark is already installed"
elif [ $retval -eq 3 ]; then
	echo -e "$WARN I couldn't locate Spark on your system. I'll install it now!"
	install_spark
else
	si="q"
        echo -e "$INFO I recommend Spark 1.6.2 to be installed on your system. Your existing installation didn't meet the required criteria."
        while [ "x$si" != "x" ]; do
                read -p $'[\e[33mWARN\e[0m] Shall I (c)ontinue with the existing Spark installation or (i)nstall Spark 1.6.2. [c/i]: ' si
                case $si in
                        [iI]* ) install_spark; break;;
                        [cC]* ) break;;
                        * ) si="q";;
                esac
        done
fi

install_datashark
echo -e "## END OF VARIABLES BY DATASHARK" >> $BASHRC_FILE
