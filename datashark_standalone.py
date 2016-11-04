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

import re
import os
import sys
import imp
import json
import argparse

from configobj import ConfigObj
from glob import glob
	
CONF_DIR = "conf"
CODE_DIR = os.path.dirname(os.path.realpath(__file__))

from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.mllib.clustering import KMeans
from pyspark.streaming.kafka import KafkaUtils

def logFilter(line, conf):
        if 'include' in conf:
                for key, value in conf['include'].iteritems():
                        if not re.match(value, json.loads(line[1])[key]):
                                return False
        if 'exclude' in conf:
                for key, value in conf['exclude'].iteritems():
                        if re.match(value, json.loads(line[1])[key]):
                                return False
        return True

if __name__ == "__main__":

	output_plugins = glob("plugins/output/out_*.py")
	sys.path.append("%s/plugins/output" % CODE_DIR)
	for plug in output_plugins:
		module = os.path.splitext(os.path.basename(plug))[0]
		locals()[module] = __import__(module)


	try:
		CONF_FILE = sys.argv[1]
	except:
		print "Please provide a conf file from the conf folder"
		sys.exit(0)

	loaded = {}
	try:
		conf = ConfigObj(CONF_FILE)
		loaded[CONF_FILE] = conf
	except:
		print "Invalid Conf"
		sys.exit(0)

	print "Loaded Confs: %s" % loaded.keys()

	sc = SparkContext(appName="dataShark Standalone")

	accum = sc.accumulator(0)
	
	config = ConfigObj("%s/datashark.conf" % CODE_DIR)

	try:
		DEBUG_MODE = sys.argv[2]
		if DEBUG_MODE == "debug":
			DEBUG_MODE = True
		else:
			DEBUG_MODE = False
	except:
		DEBUG_MODE = False

	KAFKA_HOST = config.get('zookeeper.host', None)
	KAFKA_PORT = config.get('zookeeper.port', None)
	KAFKA_SRC = "%s:%s" % (KAFKA_HOST, KAFKA_PORT)
	KAFKA_CONSUMER_NAME = config.get("kafka.consumer.name", "kafka-consumer-driver")
	KAFKA_QUEUE_NAME = config.get('kafka.queue.name', None)
	KAFKA_PARTITIONS = int(config.get('kafka.partitions', 1))
	HDFS_HOST = config.get('hdfs.host', None)
	HDFS_PORT = config.get('hdfs.port', None)

	RUN_STREAMING = False
        RUN_BATCH = False

        for cfile, conf in loaded.iteritems():
                if conf['type'] == "streaming":
                        RUN_STREAMING = True
                if conf['type'] == "batch":
                        RUN_BATCH = True

	include_path = glob("%s/conf/*" % CODE_DIR)
	for ipath in include_path:
		if not ipath.endswith(".py") and not ipath.endswith(".pyc"):
			sys.path.insert(0, ipath)

        if RUN_BATCH:
                for cfile, conf in loaded.iteritems():
			if conf['type'] == "batch":
				filename, extension = os.path.splitext(conf['code'])
				loader = __import__(filename)
				cfile = cfile.split("/")
				del cfile[-1]
				cfile = "/".join(cfile)
				batchData = sc.textFile("%s/%s/%s" % (CODE_DIR, cfile, conf['file']))
				dataRDD = loader.load(batchData)
				if DEBUG_MODE:
					print dataRDD.collect()
				else:
					output_module = conf['output']
					output = locals()['out_%s' % output_module]
					out_module = output.Plugin(conf.get("out_%s" % conf['output'], {}))
					out_module.save(dataRDD, conf['type'])

	if RUN_STREAMING:
		ssc = StreamingContext(sc, 1)
		ssc.checkpoint('/tmp/ckpt')
		
		streamingData = KafkaUtils.createStream(ssc, KAFKA_SRC, KAFKA_CONSUMER_NAME, {KAFKA_QUEUE_NAME: KAFKA_PARTITIONS})
		for cfile, conf in loaded.iteritems():
			if conf['type'] == "streaming":
				overrideStreamingData = None
				if "input" in conf:
					input_type = conf['input']
					input_conf = conf["in_%s" % input_type]
					if input_type == "kafka":
						overrideStreamingData = KafkaUtils.createStream(ssc, "%s:%s" % (input_conf['host'], input_conf['port']), KAFKA_CONSUMER_NAME, {input_conf['topic']: int(input_conf['partitions'])})
					elif input_type == "file":
						overrideStreamingData = ssc.textFileStream(input_conf['folder_path'])
				filename, extension = os.path.splitext(conf['code'])
				loader = __import__(filename)
				filters = conf.get('log_filter', None)
				if overrideStreamingData:
					localStream = overrideStreamingData
				else:
					localStream = streamingData
				if filters:
					localStream = localStream.filter(lambda line: logFilter(line, filters))
				print " - Starting %s" % conf['name']
				output_module = conf['output']
				print "   + Output Module: %s" % str(output_module).title()
				cfile = cfile.split("/")
                                del cfile[-1]
                                cfile = "/".join(cfile)
				trainingData = sc.textFile("%s/%s/%s" % (CODE_DIR, cfile, conf['training']))
				dataRDD = loader.load(localStream, trainingData, context = sc)
				if DEBUG_MODE:
					dataRDD.pprint()
				else:		
					output = locals()['out_%s' % output_module]
					out_module = output.Plugin(conf.get("out_%s" % conf['output'], {}))
					out_module.save(dataRDD, conf['type'])

		ssc.start()
		ssc.awaitTermination()

        sc.stop()
