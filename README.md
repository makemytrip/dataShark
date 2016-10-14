dataShark
=========

Table of Contents
-----------------

  * [dataShark](#datashark)
  * [Getting Started](#getting-started)
      * [Installing Dependencies](#installing-dependencies)
      * [Running dataShark in Standalone Mode](#running-datashark-in-standalone-mode)
      * [Running dataShark in Production Mode](#running-datashark-in-production-mode)
  * [Structure of dataShark](#structure-of-datashark)
    * [The Directory Structure](#the-directory-structure)
      * [datashark.py](#datasharkpy)
      * [datashark.conf](#datasharkconf)
      * [start.sh](#startsh)
      * [datashark_standalone.py](#datashark_standalonepy)
      * [datashark-env.sh](#datashark-envsh)
      * [standalone.sh](#standalonesh)
      * [conf/](#conf)
      * [conf/wordcount/wordcount[.py|.conf|.txt]](#confwordcountwordcountpyconftxt)
      * [lib/](#lib)
      * [plugins/output/](#pluginsoutput)
  * [Writing your own use cases using dataShark](#writing-your-own-use-cases-using-datashark)
    * [The .conf File](#the-conf-file)
      * [Required Keys](#required-keys)
      * [Optional Keys](#optional-keys)
    * [The .py file](#the-py-file)
  * [Output Plugins](#output-plugins)
      * [1. Elasticsearch Output Plugin](#1-elasticsearch-output-plugin)
      * [2. Syslog Output Plugin](#2-syslog-output-plugin)
      * [3. CSV Output Plugin](#3-csv-output-plugin)
  * [Contacts](#contacts)
  * [License](#license)
  * [Authors](#authors)

dataShark
=========

dataShark is a Security & Network Event Analytics Framework built on Apache Spark that enables security researchers, big data analysts and operations teams to carry out the below tasks with minimal effort:

1. Data ingest from various sources such as file system, Syslog, Kafka.
2. Write custom map / reduce and ML algorithms that operate on ingested data using abstracted Apache Spark functionality.
3. The output of the above operations can be sent to destinations such as syslog, elasticsearch and can also be persisted in the file system or HDFS.

dataShark has the following two operation modes:

1. **Standalone executable**: allows one-shot analysis of static data (input can be file system or HDFS and output can be any of the available output plugins - Syslog, Elasticsearch, file system, HDFS).
2. **Production**: full-fledged production deployment with all components (refer next section) that can ingest data from the mentioned sources.

We recommend the following components while running dataShark in production:

1. *Event Acquisition*: this layer leverages Fluentd for processing events via syslog, parsing them as per user-defined grok patterns and forwarding the same to Kafka for queuing.
2. *Event Queuing*: this layer uses Kafka to queue events for Spark to process. Often useful when the input EPS is high and the Spark layer has a delay in processing.
3. *Core Data Engine*: this is the core dataShark framework built on Spark. A user can deploy custom map / reduce or ML use cases and submit the output via any available output plugin.
4. *Persistence Layer*: elasticsearch and HDFS are leveraged to persist output and lookup data as required.
5. *Alerting Engine*: this uses ElastAlert to monitor output data and configure custom rules / thresholds to generate alerts.
6. *Output Plugins*: these are used by the Core Data Engine to persist or send its output to various destinations such as CSV, Syslog or Elasticsearch.

> *Note*: 1, 2, 4 and 5 are purely basis our experience with the production setup. One is free to use any available alternative.

[![](https://makemytrip.github.io/images/dataShark_arch.jpg)]()

**Input Data Sources:**

1. *File system*: static files to carry out one-time analysis or to train data models for ML.
2. *Kafka*: stream data that is ingested using Spark stream processing capabilities.

**Output plugins:**

1. *CSV (File system or HDFS)*: persist output data in CSV file format on the file system or HDFS.
2. *Syslog*: send output data to a remote syslog server.
3. *Elasticsearch*: persist output data in elasticsearch.

**Sample use cases / implementations:**

1. Detecting bots or anomalous server behavior using K-means classification and anomaly detection techniques.
2. Generating a summary of websites accessed using map / reduce on web proxy logs.
3. Generating a summary of web and network traffic using map / reduce on Apache HTTPD and firewall logs.


Getting Started
=============

This section describes how to get started with dataShark. Before you can actually run dataShark, there are some prerequisites that need to be installed. 

dataShark can run in 2 modes:

1. Standalone Mode
2. Production Mode

Following are the requirements for Standlone Mode Setup:

1. pySpark
2. Python Dependencies

Following are the requirements for Production Mode Setup:

1. pySpark
2. Python Dependencies
3. Kafka
4. Hadoop
5. Fluent

### Installing Dependencies

1. **pySpark** is the brains of dataShark. We recommend installing Spark with Oracle's Java >= 1.8.0. Use the following link to setup up pySpark: [https://github.com/KristianHolsheimer/pyspark-setup-guide](https://github.com/KristianHolsheimer/pyspark-setup-guide). This document provides the easiest method of setting up Spark with pySpark.
   - *[Optional]* Setting up Spark Cluster: Although it is highly recommended for better performance to setup Spark Cluster, this step is completely optional basis infrastructure availability. Following link provides steps to setup a basic Spark Cluster: [http://blog.insightdatalabs.com/spark-cluster-step-by-step/](http://blog.insightdatalabs.com/spark-cluster-step-by-step/).
   - *Note*: It is required to set the SPARK_HOME environment variable. Make sure you set it as mentioned in the install guide mentioned above.
2. **Python Dependencies** are needed to be installed to run dataShark. To install the required dependencies, run the following command: `pip install configobj argparse`
3. **Kafka** provides the high throughput message queue functionality which gets loaded to dataShark as a continuous stream for analysis. Kafka can be setup either with multiple brokers across multiple nodes or on a single node with multiple brokers, the basic setup steps are fairly the same for both methods. Following link can be used to setup multiple brokers on a single node: [http://www.michael-noll.com/blog/2013/03/13/running-a-multi-broker-apache-kafka-cluster-on-a-single-node/](http://www.michael-noll.com/blog/2013/03/13/running-a-multi-broker-apache-kafka-cluster-on-a-single-node/).
4. **Hadoop** is the resilient storage for spark that's used for checkpointing and also as a driver for starting up dataShark with all dependencies. Following link provides steps to setup a multi-node Hadoop Cluster: [http://www.michael-noll.com/tutorials/running-hadoop-on-ubuntu-linux-multi-node-cluster/](http://www.michael-noll.com/tutorials/running-hadoop-on-ubuntu-linux-multi-node-cluster/).
5. **Fluentd** is the data aggregator that collects logs from multiple sources and sends them to Kafka for consumption. Setting up fluentd is pretty easy. Fluentd's website provides steps for installation for all platforms. The Installation document can be found here: [http://docs.fluentd.org/v0.12/categories/installation](http://docs.fluentd.org/v0.12/categories/installation).

### Running dataShark in Standalone Mode

dataShark has a standalone mode for testing out use cases before plugging them in. The basic requirement to get dataShark running in standalone mode is having Apache Spark installed on the system hosting dataShark. 

Once we have all these prerequisites setup, to run dataShark in Standalone Mode you first need to clone this git repository:

```
git clone https://github.com/makemytrip/dataShark.git
```

After cloning, executing a use case in standalone mode is as easy as running the following command:

```
./standalone.sh conf/use_case_dir/sample_use_case.conf
```

Following is the sample output for a sample Standalone Mode run:

```

               __      __        _____ __               __
          ____/ /___ _/ /_____ _/ ___// /_  ____ ______/ /__
         / __  / __ `/ __/ __ `/\__ \/ __ \/ __ `/ ___/ //_/
        / /_/ / /_/ / /_/ /_/ /___/ / / / / /_/ / /  / ,<
        \__,_/\__,_/\__/\__,_//____/_/ /_/\__,_/_/  /_/|_|

                          STANDALONE MODE

                               v1.0


Loaded Confs: ['conf/wordcount/wordcount.conf']
2016-10-14 13:01:39 - (Word Count) - Written 1384 Documents to CSV File /tmp/usecase1.csv
```

### Running dataShark in Production Mode

Once we have all these prerequisites setup, to run dataShark in Production Mode you first need to clone this git repository:

```
git clone https://github.com/makemytrip/dataShark.git
```

Then we need to change the `datashark.conf` to specify the Zookeeper Host, Kafka Topic Name and HDFS Host Information. An example of sample configuration is given below:

```
zookeeper.host = 127.0.0.1
zookeeper.port = 2181

kafka.consumer.name = consumer-datashark
kafka.queue.name = logs_queue
kafka.partitions = 1

hdfs.host = 127.0.0.1
hdfs.port = 9000
```

Then we need to specify the Spark Master in datashark-env.sh:

```
SPARK_INSTANCE=spark://127.0.0.1:7077
```

This is all that is needed to install and configure datashark. To start the spark engine and use cases, we can simply run the command:

```
./start.sh
```

On the first run, we only have the Word Count Use Case enabled that will be run.
Following is the sample output of the first run:

```

               __      __        _____ __               __
          ____/ /___ _/ /_____ _/ ___// /_  ____ ______/ /__
         / __  / __ `/ __/ __ `/\__ \/ __ \/ __ `/ ___/ //_/
        / /_/ / /_/ / /_/ /_/ /___/ / / / / /_/ / /  / ,<
        \__,_/\__,_/\__/\__,_//____/_/ /_/\__,_/_/  /_/|_|

                          PRODUCTION MODE

                               v1.0


[*] 2016-10-12 14:59:06 Running Spark on Cluster
[*] 2016-10-12 14:59:06 Preparing FileSystem
[*] 2016-10-12 14:59:12 Starting Spark
Loaded Confs: ['/opt/dataShark/conf/wordcount/wordcount.conf']
2016-10-12 14:59:21 - (Word Count) - Written 1384 Documents to CSV File /tmp/usecase1.csv
 * Skip Stream Processing
[*] 2016-10-12 14:59:23 Cleaning Up
```

Structure of dataShark
======================

This section describes the structure of directories and files.

The Directory Structure
-----------------------

Following is the basic directory structure of dataShark after deployment.

```
dataShark/
├── conf
│   ├── __init__.py
│   └── wordcount
│       ├── __init__.py
│       ├── wordcount.conf
│       ├── wordcount.py
│       └── wordcount.txt
├── datashark.conf
├── datashark.py
├── datashark_standalone.py
├── datashark-env.sh
├── lib
│   ├── elasticsearch-hadoop-2.2.0.jar
│   └── spark-streaming-kafka-assembly-1.6.1.jar
├── plugins
│   ├── __init__.py
│   └── output
│       ├── __init__.py
│       ├── out_csv.py
│       ├── out_elasticsearch.py
│       └── out_syslog.py
├── start.sh
└── standalone.sh
```

Files and directories have been explained below:

### datashark.py
The heart of dataShark, this is where the magic happens. When using dataShark, you will *never* have to change the contents of this file.

### datashark.conf
The main configuration file which specifies the Kafka Queue to be consumed for Streaming Use Cases.

### start.sh
The shell file that is used to start up spark with all its dependencies and use cases.

### datashark_standalone.py
This file is used for testing individual use cases before integrating them as plugins to dataShark. 

### datashark-env.sh
This file gets loaded before execution of any Use Cases. Here you may place any required environment variables to be used by dataShark. One important variable to be set in this file is the SPARK_INSTANCE variable, that sets the spark master Host and Port.

### standalone.sh
This script is the helper for datashark_standalone.py. This loads all environment variables for executing a Use Case. You can write an use case as usual and execute it using the command, `./standalone.sh conf/use_case_dir/sample_use_case.conf` to just execute that use case. This file ignores the enabled flag in the conf, so it is advised to keep the flag set to false while doing a dry run to avoid accidental execution of the use case.

### conf/
This directory is where all use cases are placed. Refer to [Writing your own use cases using dataShark](#writing-your-own-use-cases-using-datashark) on how to write your own plugin use cases.

### conf/wordcount/wordcount[.py|.conf|.txt]
Wordcount is a sample use case provided with dataShark for trying out batch processing. The wordcount.txt file is a standard GNUv3 License file.

### lib/
Any external jar dependencies that need to be included with spark for your use cases. Out of the box, we provide you 2 jars included with datashark, Spark Streaming Kafka Library and Elasticsearch Library.

### plugins/output/
All output plugins are placed in this directory. The naming convention for files in this directory is `out_<plugin name>.py`, example, out_csv.py. Three output plugins are provided out of the box:
1. Elasticsearch
2. Syslog
3. CSV


Writing your own use cases using dataShark
===================

This document describes how to create your own use cases using dataShark. All custom code resides in the `conf` folder of dataShark.

First create a folder with the use case name (all lower case characters and underscore only) in the conf folder. To write a new use case, at the bare minimum, we need 2 files in its own folder:
> 1. The **.conf file**
> 2. A code **.py file**

The .conf file needs to define a few necessary flags specific to the use case and the .py file needs to implement the `load` function.

The .conf File
--------------------

This is what a standard .conf file looks like:

```
name = Use Case 1
type = streaming
code = code.py
enabled = true
training = training.log
output = elasticsearch
[log_filter]
        [[include]]
                some_key = ^regex pattern$
        [[exclude]]
                some_other_key = ^regex pattern$
[elasticsearch]
        host = 10.0.0.1
        port = 9200
        index_name = logstash-index
        doc_type = docs
        pkey = sourceip
        score = anomaly_score
        title = Name for ES Document
        debug = false
```

### Required Keys
`name` : Name for the Use Case.
`type` : This can be either of **batch** or **streaming**. When using *batch* mode, the use case is run just once on the provided data file. In *streaming* mode a Kafka Stream is passed to the code file to analyze.
`enabled` : Set this to either **true** or **false** to simply enable or disable this use case.
`code` : The .py file corresponding to this use case.
`training` : The log file to supply as training data to train your model. This is required only when `type = streaming`. (In batch mode, this key can be skipped)
`file` : The data file to use for *batch* processing. This is required only when `type = batch`. (In streaming mode, this key can be skipped)
`output` : The output plugin to use. Types of output plugins are listed below.
`[type_of_plugin]` : The settings for the output plugin being used.

### Optional Keys
`[log_filter]` : This is used to filter out the Kafka stream passed to your use case. It has the following two optional sub-sections:
- `[[include]]` : In this sub-section each key value pair is used to filter the incoming log stream to include in the use case. The *key* is the name of the key in the JSON Document in the Kafka Stream. The *value* has to be a regex pattern that matches the content of that key.
- `[[exclude]]` : In this sub-section each key value pair is used to filter the incoming log stream to exclude from the use case. The *key* is the name of the key in the JSON Document in the Kafka Stream. The *value* has to be a regex pattern that matches the content of that key.

The .py file
----------------
The .py file is the brains of the system. This is where all the map-reduce. model training happens. The user needs to implement a method named `load` in this .py file. dataShark provides two flavors of the load function to implement, one for streaming and one for batch processing. Following is the basic definition of the load function of each type:

*For batch processing:*

```
def load(batchData)
```
The data file provided as input in the .conf file is loaded and passed to the function in the variable batchData. batchData is of type `PythonRDD`.

*For stream processing:*

```
def load(streamingData, trainingData, context)
```

`streamingData` is the Kafka Stream being sent to the function load. This is of type *DStream*.
`trainingData` is the Training File loaded from the *training* key mention in the .conf file. It is of the type *PythonRDD*.
`context` is the spark context loaded in the driver. It may be used for using the accumulator, etc.

The function `load` expects a processed *DStream* to be returned from it. Each RDD in the DStream should be in the following format (this format is necessary for usability in output plugins):
`('primary_key', anomaly_score, {"some_metadata": "dictionary here"})`

*primary_key* is a string. It is the tagging metric by which the data was aggregated for map-reduce and finally scored.
*anomaly_score* is of type float. It is the value used to define the deviation from normal behavior.
*metadata* is of the type dictionary. This is the extra data that needs to be inserted into the Elasticsearch document or added to the CSV as extra Columns.

-------------------
 
Output Plugins
=============
dataShark provides the following 3 output plugins out-of-the-box for processed data persistence or transmission:

1. Elasticsearch
2. Syslog
3. CSV

Each of this plugin requires its own basic set of settings, described below.

### 1. Elasticsearch Output Plugin

The Elasticsearch output plugin allows you to easily push JSON documents to your Elasticsearch Node. This allows users to build visualizations using Kibana over processed data.

Following is the basic template for configuring Elasticsearch output plugin:

```
output = elasticsearch
[elasticsearch]
        host = 127.0.0.1
        port = 9200
        index_name = usecase
        doc_type = spark-driver
        pkey = source_ip
        score = anomaly_score
        title = Use Case
        debug = false
```

All settings in the config are optional. Their default values are displayed in the config above.

	`host` : Host IP or Hostname or the ES server.
	`port` : Port Number of ES Server.
	`index_name` : Name of the index to push documents to for this use case.
	`doc_type` : Document Type Name for this use case.
	`pkey` : Primary Key Field name to show in ES Document.
	`score` : Anomaly Score Key Field Name to show in ES Document.
	`title` : The value of the title field in the ES Document.
	`debug` : Set this to true to display each JSON record being push to ES on the console.

### 2. Syslog Output Plugin

The Syslog Output plugin outputs JSON documents to the specified Syslog Server IP and Port. Following is the sample configuration with default settings for the plugin (all settings are optional):

```
output = syslog
[syslog]
        host = 127.0.0.1
        port = 514
        pkey = source_ip
        score = anomaly_score
        title = Use Case Title
        debug = false
```

The settings are similar to that of elasticsearch.

### 3. CSV Output Plugin

The CSV Output Plugins writes and appends output from Spark Use Case to a specified CSV File. Following is the sample configuration with default settings of the plugin (all settings are optional):

```
output = csv
[csv]
        path = UseCase.csv
        separator = ,
        quote_char = '"'
        title = Use Case
        debug = false
```

Contacts
========

Discussion / Forum: [https://groups.google.com/forum/#!forum/datashark](https://groups.google.com/forum/#!forum/datashark)
For anything else: datashark@makemytrip.com

License
=======

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details. [http://www.gnu.org/licenses/](http://www.gnu.org/licenses/).

[![](https://www.gnu.org/graphics/gplv3-127x51.png)](https://www.gnu.org/licenses/gpl.txt)

Authors
=======

- [Kunal Aggarwal](https://twitter.com/KunalAggarwal92)
- [Dhruv Kalaan](https://twitter.com/dkalaan)
- [Vikram Mehta](https://twitter.com/vikramm811)
