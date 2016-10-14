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

if [ -z ${SPARK_HOME} ];
then
	echo "SPARK_HOME environment vairable is unset. Please set SPARK_HOME";
	exit 1;
fi

############ DO NOT MODIFY ANYTHING ABOVE THIS LINE ############

SPARK_INSTANCE="spark://127.0.0.1:7077"
