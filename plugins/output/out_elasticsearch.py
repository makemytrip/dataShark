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
import json

class Plugin:

	def __init__(self, conf):
		self.host 	= conf.get('host', '127.0.0.1')
		self.port 	= conf.get('port', '9200')
		self.pkey 	= conf.get('pkey', 'source_ip')
		self.doc_type 	= conf.get('doc_type', 'spark-driver')
		self.index_name = conf.get('index_name', 'usecase')
		self.score 	= conf.get('score', 'anomaly_score')
		self.title 	= conf.get('title', 'Use Case')
		self.debug = conf.get('debug', False)
                if self.debug == "true":
                        self.debug = True
                else:
                        self.debug = False
		
		self.es_conf = {
			"es.nodes" : self.host,
	                "es.port" : self.port,
        	        "es.resource" : "%s/%s" % (self.index_name, self.doc_type)
		}

		if "options" in conf:
			for key, val in conf['options'].iteritems():
				self.es_conf[key] = val

	def save(self, dataRDD, progType):
		if progType == "streaming":
			dataRDD.foreachRDD(lambda s: self.__save(s))
                elif progType == "batch":
                        self.__save(dataRDD)

	def __save(self, dataRDD):
		data = dataRDD.map(lambda s: self.__save_to_es(s))
                if self.debug:
			for row in data.collect():
				print row[1]
                try:
			if data.collect():
				data.saveAsNewAPIHadoopFile(
					path = '-',
					keyClass = "org.apache.hadoop.io.NullWritable",
					valueClass = "org.elasticsearch.hadoop.mr.LinkedMapWritable",
					outputFormatClass = "org.elasticsearch.hadoop.mr.EsOutputFormat",
					conf = self.es_conf
				)
				print "%s - (%s) - Inserted %s Documents in Elasticsearch %s:%s " % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.title, len(data.collect()), self.host, self.port)
			else:
				print "%s - (%s) - No RDD Data Recieved" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.title)
                except Exception as e:
			print e
                        print "Error saving to Elasticsearch"

	def __save_to_es(self, row):
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
		if "es.input.json" in self.es_conf:
			if self.es_conf['es.input.json'] == "true":
				return ('key', json.dumps(data))
		return ('key', data)
