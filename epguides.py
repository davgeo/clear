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

#################################################
# EPGuidesLookup
#################################################
class EPGuidesLookup:
  ALLSHOW_IDLIST_URL = 'http://epguides.com/common/allshows.txt'
  EPISODE_LOOKUP_URL = 'http://epguides.com/common/exportToCSV.asp'
  SAVE_DIR = 'test_dir'

  #################################################
  # constructor
  #################################################
  def __init__(self):
    self._allShowList = None
    self._showInfoDict = {}
    self._showTitleList = None
    self._showIDList = None

  # *** INTERNAL CLASSES *** #
  ############################################################################
  # _GetAllShowList
  # Populates self._allShowList with the EPGuides all show info
  # On the first lookup for a day the information will be loaded from
  # the EPGuides url. This will be saved to local file _epguides_YYYYMMDD.csv
  # and any old files will be removed. Subsequent accesses for the same day
  # will read this file.
  ############################################################################
  def _GetAllShowList(self):

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
        print("Adding new EPGUIDES file: {0}".format(saveFilePath))
        allShowsFile.write(self._allShowList)

      # Delete old copies of this file
      globPattern = '_epguides_????????.csv'
      globFilePath = os.path.join(self.SAVE_DIR, globPattern)
      for filePath in glob.glob(globFilePath):
        if filePath != saveFilePath:
          print('Removing old EPGUIDES file:', filePath)
          os.remove(filePath)

  ############################################################################
  # _GetTitleAndIDList
  # Get title and id lists from EPGuides all show info
  ############################################################################
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

  ############################################################################
  # _GetTitleList
  # Generate title list if it does not already exist
  ############################################################################
  def _GetTitleList(self):
    if self._showTitleList is None:
      self._GetTitleAndIDList()

  ############################################################################
  # _GetIDList
  # PGenerate id list if it does not already exist
  ############################################################################
  def _GetIDList(self):
    if self._showIDList is None:
      self._GetTitleAndIDList()

  ############################################################################
  # _GetShowID
  # Get EPGuides ID for showName
  ############################################################################
  def _GetShowID(self, showName):
    self._GetTitleList()
    self._GetIDList()

    for index, showTitle in enumerate(self._showTitleList):
      if showName == showTitle:
        return self._showIDList[index]
    return None

  ############################################################################
  # _ExtractDataFromShowHtml
  # Extracts show data from <html><body><pre>
  ############################################################################
  def _ExtractDataFromShowHtml(self, html):
    xmlRoot = etree.fromstring(html)
    for child in xmlRoot:
      if child.tag == 'body':
        for subChild in child:
          if subChild.tag =='pre':
            # Return text with leading and trailing whitespace stripped
            return(subChild.text.strip())
    raise Exception("Show content not found - check EPGuides html formatting")

  ############################################################################
  # _GetEpisodeName
  # Get episode name from EPGuides show info
  ############################################################################
  def _GetEpisodeName(self, showID, season, episode):
    # Load data for showID from dictionary
    showInfo = csv.reader(self._showInfoDict[showID].splitlines())
    for rowCnt, row in enumerate(showInfo):
      if rowCnt == 0:
        # Get header column index
        for colCnt, column in enumerate(row):
          if column == 'season':
            seasonIndex = colCnt
          if column == 'episode':
            episodeIndex = colCnt
          if column == 'title':
            titleIndex = colCnt
      else:
        # Iterate rows until matching season and episode found
        try:
          int(row[seasonIndex])
          int(row[episodeIndex])
        except ValueError:
          # Skip rows which don't provide integer season or episode numbers
          pass
        else:
          if int(row[seasonIndex]) == int(season) and int(row[episodeIndex]) == int(episode):
            print("Episode name is {0}".format(row[titleIndex]))
            return row[titleIndex]
    return None

  # *** EXTERNAL CLASSES *** #
  ############################################################################
  # ShowNameLookUp
  # Get closest show name match to a given string
  ############################################################################
  def ShowNameLookUp(self, string):
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

  ############################################################################
  # EpisodeNameLookUp
  # Get the episode name correspondng to the given show name, season number
  # and episode number
  ############################################################################
  def EpisodeNameLookUp(self, showName, season, episode):
    print("Looking up episode name for {0} S{1}E{2}".format(showName, season, episode))
    showID = self._GetShowID(showName)
    if showID is not None:
      try:
        self._showInfoDict[showID]
      except KeyError:
        print("Looking up info for new show: {0}(ID:{1})".format(showName, showID))
        urlData = util.WebLookup(self.EPISODE_LOOKUP_URL, {'rage': showID})
        self._showInfoDict[showID] = self._ExtractDataFromShowHtml(urlData)
      else:
        print("Reusing show info previous obtained for: {0}({1})".format(showName, showID))
      finally:
        return self._GetEpisodeName(showID, season, episode)
