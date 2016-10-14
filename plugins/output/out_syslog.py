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

from datetime import datetime
import logging
import logging.handlers
import json

class Plugin:

	def __init__(self, conf):
		self.port  = int(conf.get('port', 514))
		self.host  = conf.get('host', '127.0.0.1')
		self.pkey  = conf.get('pkey', 'source_ip')
		self.score = conf.get('score', 'anomaly_score')
		self.title = conf.get('title', 'Use Case Title')
		self.debug = conf.get('debug', False)
		if self.debug == "true":
                        self.debug = True
                else:
                        self.debug = False

	def save(self, dataRDD, progType):
		if progType == "streaming":
			dataRDD.foreachRDD(lambda s: self.__writeToSyslog(s))
                elif progType == "batch":
                        self.__writeToSyslog(dataRDD)

	def __writeToSyslog(self, dataRDD):
		data = dataRDD.map(lambda s: self.__write(s))
		if data.collect():
			my_logger = logging.getLogger('Spark-Driver')
	                my_logger.setLevel(logging.INFO)
                	handler = logging.handlers.SysLogHandler(address = (self.host, self.port), facility=13)
	                my_logger.addHandler(handler)
			for row in data.collect():
				if self.debug:
					print row
				my_logger.info(json.dumps(row[1]))
			print "%s - (%s) - Written %s Documents to Syslog %s:%s " % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.title, len(data.collect()), self.host, self.port)
		else:
			print "%s - (%s) - No RDD Data Recieved" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.title)		

	def __write(self, row):	
		data = {
                        "title": self.title,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        self.pkey: row[0],
                        self.score: row[1]
                }
		try:
	                metadata = row[2]
		except:
			metadata = {}
                data.update(metadata)
                return ('key', data)

