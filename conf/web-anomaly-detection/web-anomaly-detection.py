# Copyright 2016 MakeMyTrip (Kunal Aggarwal, Vikram Mehta)
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
from math import sqrt

from pyspark.mllib.clustering import KMeans

# Reduce Function
def make_features(a, b):
	# Add up counts of 2xx and 5xx response	against a source IP
	twoxx = a[0] + b[0]
	nxx = a[1] + b[1]

	return [twoxx, nxx]
	

# Function to process raw training and streaming data
def process_logs(data, pattern):
	line = re.match(pattern, data)
	logline = line.groupdict()

	nxx = 0
	twoxx = 0

	# If response code is 2xx, then we set the count for twoxx as 1
	if str(logline['response_code']).startswith("2"):
		twoxx = 1
	# If response code is 5xx, then we set the count for nxx is 1
	elif str(logline['response_code']).startswith("5"):
		nxx = 1

	# Return data in the form (1.1.1.1, [1, 0])
	return (logline['source'], [twoxx, nxx])


# Cluster Prediction and distance calculation
def predict_cluster(row, model):
	
	# Predict the cluster for the current data row
	cluster = model.predict(row[1])
	
	# Find the center for the current cluster
	center = model.centers[cluster]

	# Calculate the disance between the Current Row Data and Cluster Center
	distance = sqrt(sum([x ** 2 for x in (row[1] - center)]))

	return (row[0], distance, {"cluster": model.predict(row[1]), "twoxx": row[1][0], "nxx": row[1][1]})


def load(streamingData, trainingData, context, conf):

	# Process JSON Training Logs
	rawTrainingData = trainingData.map(lambda s: process_logs(s, conf['apache_access_logs_pattern']))
	
	# Reduce Training Logs to get counts of 2xx and 5xx response codes against an IP
	rawTrainingData = rawTrainingData.reduceByKey(make_features)

	# Convert data to format acceptable for K-Means
	training_set = rawTrainingData.map(lambda s: s[1])

	# Set Cluster Count to 2
	k = 2 

	# Train the K-Means Model with Training Data
	model = KMeans.train(training_set, k)

	# Print out centers of the trained model
	for i in range(k):
		print model.centers[i]
	
	# Process incoming JSON Logs from Kafka Stream
        rawTestingData = streamingData.map(lambda s: process_logs(s, conf['apache_access_logs_pattern']))

	# Reduce 60 seconds of incoming data in a 60 seconds sliding window and calculate distance from cluster center it belongs to
        testing_data = rawTestingData.reduceByKeyAndWindow(make_features, lambda a, b: [a[0] - b[0], a[1] - b[1]], 60, 60).map(lambda s: predict_cluster(s, model))

	return testing_data
