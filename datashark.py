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
import uuid
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

	output_plugins = glob("out_*.py")
	for plug in output_plugins:
		module = os.path.splitext(plug)[0]
		locals()[module] = __import__(module)

	parser = argparse.ArgumentParser(description='Spark Driver Program')
        parser.add_argument('--local', action = 'store_true', help = 'Run this spark instance on local Spark machine')
        args = parser.parse_args()

	conf_files = glob("%s/conf/*/*.conf" % CODE_DIR)
	loaded = {}

	try:
		for i in conf_files:
			conf = ConfigObj(i)
			if conf['enabled'] == "true":
				loaded[i] = conf
	except:
		print "Could not load : %s" % i

	print "Loaded Confs: %s" % loaded.keys()

	token = str(uuid.uuid4()).upper()
	app_name = "dataShark_%s" % token
	print "App Name: %s" % app_name

	config = ConfigObj("%s/datashark.conf" % CODE_DIR)
	
	spark_conf_dict = config.get("spark_config", {})
	conf = SparkConf()
	for key, val in spark_conf_dict.iteritems():
		conf = conf.set(key, val)

	sc = SparkContext(appName = app_name, conf = conf)

	accum = sc.accumulator(0)

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
				batchData = sc.textFile("hdfs://%s:%s/user/root/driverFiles/%s" % (HDFS_HOST, HDFS_PORT, conf['file']))
				dataRDD = loader.load(batchData)
				output_module = conf['output']
				output = locals()['out_%s' % output_module]
				out_module = output.Plugin(conf.get("out_%s" % conf['output'], {}))
				out_module.save(dataRDD, conf['type'])
        else:
                print " * Skipping Batch Processing"

	if RUN_STREAMING:
		ssc = StreamingContext(sc, 1)
		if args.local:
			ssc.checkpoint('ckpt')
		else:
			ssc.checkpoint('hdfs://%s:%s/user/root/ckpt' % (HDFS_HOST, HDFS_PORT))
		
		streamingData = KafkaUtils.createStream(ssc, KAFKA_SRC, "%s_%s" % (KAFKA_CONSUMER_NAME, token), {KAFKA_QUEUE_NAME: KAFKA_PARTITIONS}).cache()
		for cfile, conf in loaded.iteritems():
			if conf['type'] == "streaming":
				overrideStreamingData = None
                                if "input" in conf:
                                        input_type = conf['input']
                                        input_conf = conf["in_%s" % input_type]
                                        if input_type == "kafka":
                                                overrideStreamingData = KafkaUtils.createStream(ssc, "%s:%s" % (input_conf['host'], input_conf['port']), "%s_%s" % (KAFKA_CONSUMER_NAME, token), {input_conf['topic']: int(input_conf['partitions'])}).cache()
                                        elif input_type == "file":
                                                overrideStreamingData = ssc.textFileStream(input_conf['folder_path']).cache()
				filename, extension = os.path.splitext(conf['code'])
				loader = __import__(filename)
				filters = conf.get('log_filter', None)
				localStream = streamingData
				if filters:
					localStream = localStream.filter(lambda line: logFilter(line, filters))
				print " - Starting %s" % conf['name']
				output_module = conf['output']
				print "   + Output Module: %s" % str(output_module).title()
				if os.path.exists("%s/%s" % (CONF_DIR, conf['training'])):
					training_log_file = "%s/%s/%s" % (CODE_DIR, CONF_DIR, conf['training'])
				else:
					training_log_file = "%s/%s" % (CODE_DIR, conf['training'])
				trainingData = sc.textFile("hdfs://%s:%s/user/root/driverFiles/%s" % (HDFS_HOST, HDFS_PORT, conf['training']))
				dataRDD = loader.load(localStream, trainingData, context = sc)
				
				output = locals()['out_%s' % output_module]
				out_module = output.Plugin(conf.get("out_%s" % conf['output'], {}))
				out_module.save(dataRDD, conf['type'])

		ssc.start()
		ssc.awaitTermination()
	else:
                print " * Skip Stream Processing"

        sc.stop()
