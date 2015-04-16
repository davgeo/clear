''' EPGUIDES '''
# Python default package imports
import os
import glob
import csv
import datetime
import xml.etree.ElementTree as etree

# Custom Python package imports

# Local file imports
import util

class EPGuidesLookup:
  ALLSHOW_IDLIST_URL = 'http://epguides.com/common/allshows.txt'
  EPISODE_LOOKUP_URL = 'http://epguides.com/common/exportToCSV.asp'
  SAVE_DIR = 'test_dir'

  def __init__(self):
    self._allShowList = None
    self._showInfoDict = {}
    self._showTitleList = None
    self._showIDList = None

  def _GetAllShowList(self):
    # Populates self._allShowList with the EPGuides all show info
    # On the first lookup for a day the information will be loaded from
    # the EPGuides url. This will be saved to local file _epguides_YYYYMMDD.csv
    # and any old files will be removed. Subsequent accesses for the same day will read this file.
    today = datetime.date.today().strftime("%Y%m%d")
    saveFile = '_epguides_' + today + '.csv'
    saveFilePath = os.path.join(self.SAVE_DIR, saveFile)
    if os.path.exists(saveFilePath):
      # Load data previous saved to file
      with open(saveFilePath, 'r') as allShowsFile:
        self._allShowList = allShowsFile.read()
    else:
      # Download new list from EPGUIDES and strip any leading or trailing whitespace
      self._allShowList = util.WebLookup(self.ALLSHOW_IDLIST_URL).strip()

      # Save to file to avoid multiple url requests in same day
      with open(saveFilePath, 'w') as allShowsFile:
        allShowsFile.write(self._allShowList)

      # Delete old copies of this file
      globPattern = '_epguides_????????.csv'
      globFilePath = os.path.join(self.SAVE_DIR, globPattern)
      for filePath in glob.glob(globFilePath):
        if filePath != saveFilePath:
          print('Removing old EPGUIDES file:', filePath)
          os.remove(filePath)

  def _GetTitleAndIDList(self):
    # Populate self._allShowList if it does not already exist
    if self._allShowList is None:
      self._GetAllShowList()

    self._showTitleList = []
    self._showIDList = []

    # Read self._allShowList as csv file
    csvReader = csv.reader(self._allShowList.splitlines())
    for rowCnt, row in enumerate(csvReader):
      if rowCnt == 0:
        # Get header column index
        for colCnt, column in enumerate(row):
          if column == 'title':
            titleIndex = colCnt
          if column == 'tvrage':
            rageIndex = colCnt
      else:
        # Make list of all titles
        self._showTitleList.append(row[titleIndex])
        self._showIDList.append(row[rageIndex])

  def _GetTitleList(self):
    if self._showTitleList is None:
      self._GetTitleAndIDList()

  def _GetIDList(self):
    if self._showIDList is None:
      self._GetTitleAndIDList()

  def ShowNameLookUp(self, string):
    # Look up EPGuides show name for given string

    self._GetTitleList()

    # Get title which has the best match to showName
    ratioMatch = []
    for title in self._showTitleList:
      ratioMatch.append(util.GetBestStringMatchValue(string, title))

    maxRatio = max(ratioMatch)
    matchTitleIndex = [i for i, j in enumerate(ratioMatch) if j == maxRatio]

    showName = []
    for index in matchTitleIndex:
      showName.append(self._showTitleList[index])

    return(showName)
