# -*- coding: utf-8 -*-

from __future__ import division
import argparse
import sys
import sqlite3
import csv
import droid2sqlite
import MsoftFnameAnalysis
from urlparse import urlparse

class DROIDAnalysis:

	# DB self.cursor
	cursor = None

	# Counts
	filecount = 0
	containercount = 0
	filesincontainercount = 0	
	foldercount = 0
	uniquedircount = 0
	identifiedfilecount = 0
	unidentifiedcount = 0
	zeroidcount = 0
	extensionIDOnlyCount = 0
	distinctextensioncount = 0
	distinctextpuidcount = 0
	distinctbinpuidcount = 0

	def __countQuery__(self, query):
		self.cursor.execute(query)
		count = self.cursor.fetchone()[0]
		print "XXX: " + str(count)
		return count

	def __listQuery__(self, query, separator):
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		row = ""
		for r in result:
			if len(r) > 1:
				item = ""
				for t in r:
					item = item + str(t) + ", "
				row = row + item[:-2] + separator
			else:
				row = row + str(r[0]) + separator 
		print row[:-2]

	def __alternativeFrequencyQuery__(self, query):
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		return result

	def countFilesQuery(self):
		self.filecount = self.__countQuery__( 
			"SELECT COUNT(NAME) FROM droid WHERE (TYPE='File' OR TYPE='Container')")

	# Container objects known by DROID...
	def countContainerObjects(self):
		self.containercount = self.__countQuery__(
			"SELECT COUNT(NAME) FROM droid WHERE TYPE='Container'")
	
	def countFilesInContainerObjects(self):
		self.filesincontainercount = self.__countQuery__( 
			"SELECT COUNT(NAME) FROM droid WHERE URI_SCHEME!='file' AND (TYPE='File' OR TYPE='Container')")

	def countUniqueDirs(self):
		self.uniquedirs = self.__countQuery__( 
			"SELECT COUNT(DISTINCT DIR_NAME) FROM droid")

	def countIdentifiedQuery(self):
		self.identifiedfilecount = self.__countQuery__( 
			"SELECT COUNT(NAME) FROM droid WHERE (TYPE='File' OR TYPE='Container') AND (METHOD='Signature' or METHOD='Container')")

	def countTotalUnidentifiedQuery(self):
		self.unidentifiedfilecount = self.__countQuery__( 
			"SELECT COUNT(NAME) FROM droid WHERE (TYPE='File' OR TYPE='Container') AND (METHOD='no value' OR METHOD='Extension')")	
	
	def countFoldersQuery(self):
		self.foldercount = self.__countQuery__( 
			"SELECT COUNT(NAME) FROM droid WHERE TYPE='Folder'")

	def countZeroID(self):
		self.zeroidcount = self.__countQuery__( 
			"SELECT COUNT(NAME) FROM droid WHERE METHOD='no value' AND (TYPE='File' OR TYPE='Container')")

	def countExtensionIDOnly(self):
		self.extensionIDOnlyCount = self.__countQuery__( 
			"SELECT COUNT(NAME) FROM droid WHERE METHOD='Extension' AND(TYPE='File' OR TYPE='Container')")
	
	# PUIDS for files identified by DROID using binary matching techniques
	def countSignaturePUIDS(self):
		self.distinctbinpuidcount = self.__countQuery__( 
			"SELECT COUNT(DISTINCT PUID) FROM droid WHERE (TYPE='File' OR TYPE='Container') AND (METHOD='Signature' OR METHOD='Container')")
		
	def countExtensionPUIDS(self):
		self.distinctextpuidcount = self.__countQuery__( 
			"SELECT COUNT(DISTINCT PUID) FROM droid WHERE (TYPE='File' OR TYPE='Container') AND METHOD='Extension'")

	def countExtensions(self):
		self.distinctextensioncount = self.__countQuery__( 
			"SELECT COUNT(DISTINCT EXT) FROM droid WHERE TYPE='File' OR TYPE='Container'")








	# Frequency list queries
	def identifiedBinaryMatchedPUIDFrequency(self):
		self.__listQuery__( 
			"SELECT PUID, COUNT(*) AS total FROM droid WHERE (TYPE='File' OR TYPE='Container') AND (METHOD='Signature' OR METHOD='Container') GROUP BY PUID ORDER BY TOTAL DESC",  " | ")

	def extensionOnlyIdentificationFrequency(self):
		self.__listQuery__( 
			"SELECT PUID, COUNT(*) AS total FROM droid WHERE (TYPE='File' OR TYPE='Container') AND (METHOD='Extension') GROUP BY PUID ORDER BY TOTAL DESC",  " | ")

	def allExtensionsFrequency(self):
		self.__listQuery__(
			"SELECT EXT, COUNT(*) AS total FROM droid WHERE (TYPE='File' OR TYPE='Container') GROUP BY EXT ORDER BY TOTAL DESC", " | ")





	# List queries
	def listUniqueBinaryMatchedPUIDS(self):
		self.__listQuery__(
			"SELECT DISTINCT PUID FROM droid WHERE (TYPE='File' OR TYPE='Container') AND (METHOD='Signature' OR METHOD='Container')", " | ")

	def listAllUniqueExtensions(self):	
		self.__listQuery__(
			"SELECT DISTINCT EXT FROM droid WHERE (TYPE='File' OR TYPE='Container')", " | ")

	def listExtensionOnlyIdentificationPUIDS(self):	
		self.__listQuery__(		
			"SELECT DISTINCT PUID, FORMAT_NAME FROM droid WHERE (TYPE='File' OR TYPE='Container') AND METHOD='Extension'", " | ")

	def listNoIdentificationFiles(self):
		self.__listQuery__(	
			"SELECT FILE_PATH FROM droid WHERE METHOD='no value' AND (TYPE='File' OR TYPE='Container')", "\n")

	def listDuplicates(self):
		duplicatequery = "SELECT MD5_HASH, COUNT(*) AS total FROM droid WHERE (TYPE='File' OR TYPE='Container') GROUP BY MD5_HASH ORDER BY TOTAL DESC"
		result = self.__alternativeFrequencyQuery__(duplicatequery)
		for r in result:
			if r[1] > 1:
				duplicatemd5 = r[0]
				print
				print "Duplicate hash: " + duplicatemd5
				self.__listQuery__("SELECT MD5_HASH, DIR_NAME, NAME FROM droid WHERE MD5_HASH='" + duplicatemd5 + "'", "\n")






	def paretoListingPUIDS(self):
		# Hypothesis: 80% of the effects come from 20% of the causes		

		eightyPercentTotalPUIDs = int(self.identifiedfilecount * 0.80)		# 80 percent figure
		countIdentifiedPuids = "SELECT PUID, COUNT(*) AS total FROM droid WHERE (TYPE='File' OR TYPE='Container') AND (METHOD='Signature' OR METHOD='Container') GROUP BY PUID ORDER BY TOTAL DESC"
		self.listTopTwenty(self.__alternativeFrequencyQuery__(countIdentifiedPuids), eightyPercentTotalPUIDs, self.identifiedfilecount, "Identified formats", "identified formats")
		
	def paretoListingExts(self):
		# Hypothesis: 80% of the effects come from 20% of the causes		

		eightyPercentTotalExts = int(self.filecount * 0.80)		# 80 percent figure
		countExtensions = "SELECT EXT, COUNT(*) AS total FROM droid WHERE (TYPE='File' OR TYPE='Container') GROUP BY EXT ORDER BY TOTAL DESC"
		self.listTopTwenty(self.__alternativeFrequencyQuery__(countExtensions), eightyPercentTotalExts, self.filecount, "Extensions for formats", "total files")

	def listTopTwenty(self, frequencyQueryResult, eightyPercentTotal, total, introtext, endtext):

		x = 0
		index = "null"
		
		for i,t in enumerate(frequencyQueryResult):
			count = t[1]
			if count <= eightyPercentTotal:
				x = x + count
				if x >= eightyPercentTotal:
					index = i
					break
	
		if index is not "null":
			print 
			print introtext + " contributing to 20% of collection out of " + str(total) + " " + endtext
			for i in range(index):
				label = frequencyQueryResult[i][0]
				count = frequencyQueryResult[i][1]
				print label + "       COUNT: " + str(count)
	
		else:
			print "Format frequency: "
			print freqTuple[0][0] + "       COUNT: " + str(freqTuple[0][1])




	def filesWithDodgyCharacters(self):
		countDirs = "SELECT DISTINCT NAME FROM droid"
		self.cursor.execute(countDirs)
		dirlist = self.cursor.fetchall()
		charcheck = MsoftFnameAnalysis.MsoftFnameAnalysis()
		for d in dirlist:
			dirstring = d[0]
			charcheck.completeFnameAnalysis(dirstring)
		return

	# stats output... 
	def calculateIdentifiedPercent(self):
		allcount = self.filecount
		count = self.identifiedfilecount
		if allcount > 0:
			percentage = (count/allcount)*100
			print "Percentage of the collection identified: " + '%.1f' % round(percentage, 1) + "%"
		else:
			print "Zero files" 

	def calculateUnidentifiedPercent(self):
		allcount = self.filecount
		count = self.unidentifiedfilecount		
		
		print allcount
		print count
		
		
		if allcount > 0:
			percentage = (count/allcount)*100
			print "Percentage of the collection unidentified: " + '%.1f' % round(percentage, 1) + "%"
		else:
			print "Zero files" 
						
	def queryDB(self):
		self.countFilesQuery()
		self.countContainerObjects()
		self.countFilesInContainerObjects()
		self.countFoldersQuery()
		self.countIdentifiedQuery()
		self.countTotalUnidentifiedQuery()
		self.countZeroID()
		self.countExtensionIDOnly()
		self.countSignaturePUIDS()
		self.countExtensionPUIDS()
		self.countExtensions()
		self.countUniqueDirs()

		print
		print "Signature identified PUIDs in collection:"
		#self.listUniqueBinaryMatchedPUIDS()

		print
		print "Frequency of signature identified PUIDs:"
		#self.identifiedBinaryMatchedPUIDFrequency()

		print
		print "Extension only identification in collection:"
		#self.listExtensionOnlyIdentificationPUIDS()

		print 
		print "Frequency of extension only identification in collection: "
		#self.extensionOnlyIdentificationFrequency()

		print
		print "Unique extensions identified across collection:"
		#self.listAllUniqueExtensions()

		print
		print "Frequency of all extensions:"
		#self.allExtensionsFrequency()

		print
		print "List of files with no identification: "
		#self.listNoIdentificationFiles()

		print
		print "pareto: "
		#self.paretoListingPUIDS()
		print
		#self.paretoListingExts()

		print
		print "Total items in collection unidentified:"
		#self.calculateUnidentifiedPercent()
		
		print
		print "Total items in collection identified:"
		#self.calculateIdentifiedPercent()
		
		print 
		print "Listing duplicates: "
		#self.listDuplicates()

		print
		print "Identifying troublesome filenames: "
		#self.filesWithDodgyCharacters()

	def openDROIDDB(self, dbfilename):
		conn = sqlite3.connect(dbfilename)
		conn.text_factory = str		#encoded as ascii, not unicode / return ascii
		
		self.cursor = conn.cursor()
		self.queryDB()		# primary db query functions
		#self.detect_invalid_characters("s")		# need to pass strings to this... 
		conn.close()

def handleDROIDDB(dbfilename):
	analysis = DROIDAnalysis()	
	analysis.openDROIDDB(dbfilename)
	#TODO: Incorrect filetypes provided, e.g. providing CSV not DB

def handleDROIDCSV(droidcsv, analyse=False):
	dbfilename = droid2sqlite.handleDROIDCSV(droidcsv)
	if analyse == True:
		handleDROIDDB(dbfilename)

def main():

	#	Usage: 	--csv [droid report]

	#	Handle command line arguments for the script
	parser = argparse.ArgumentParser(description='Analyse DROID results stored in a SQLite DB')
	parser.add_argument('--csv', help='Optional: Single DROID CSV to read.', default=False)
	parser.add_argument('--csva', help='Optional: DROID CSV to read, and then analyse.', default=False)
	parser.add_argument('--db', help='Optional: Single DROID sqlite db to read.', default=False)

	if len(sys.argv)==1:
		parser.print_help()
		sys.exit(1)

	#	Parse arguments into namespace object to reference later in the script
	global args
	args = parser.parse_args()
	
	if args.csv:
		handleDROIDCSV(args.csv)
	if args.csva:
		handleDROIDCSV(args.csva, True)
	if args.db:
		handleDROIDDB(args.db)
	
	else:
		sys.exit(1)

if __name__ == "__main__":
	main()
