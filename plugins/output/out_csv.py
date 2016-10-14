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

import csv
from datetime import datetime

class Plugin:

	def __init__(self, conf):
		self.path = conf.get('path', 'UseCase.csv')
		self.separator = conf.get('separator', ',')
		self.quote_char = conf.get('quote_char', '"')
		self.title = conf.get('title', 'Use Case')
		self.debug = conf.get('debug', False)
                if self.debug == "true":
                        self.debug = True
                else:
                        self.debug = False

	def save(self, dataRDD, progType):
		if progType == "streaming":
			dataRDD.foreachRDD(lambda s: self.__writeToCSV(s))
		elif progType == "batch":
			self.__writeToCSV(dataRDD)
		
		
	def __writeToCSV(self, dataRDD):
		if dataRDD.collect():
			with open(self.path, 'a') as csvfile:
				spamwriter = csv.writer(csvfile, delimiter = self.separator, quotechar = self.quote_char, quoting=csv.QUOTE_MINIMAL)
				currentTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				for row in dataRDD.collect():
					if self.debug:
						print row
					csvrow = [currentTime, row[0], row[1]]
					try:
						metadata = row[2]
					except:
						metadata = {}
					if metadata:
						for key in sorted(metadata):
							csvrow.append(metadata[key])
					spamwriter.writerow(csvrow)			
			print "%s - (%s) - Written %s Documents to CSV File %s " % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.title, len(dataRDD.collect()), self.path)
		else:
			print "%s - (%s) - No RDD Data Recieved" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.title)
