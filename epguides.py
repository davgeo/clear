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
    self._idList = None
    self._showInfoDict = {}

  def _GetShowIDList(self):
    # Populates self._idList with the EPGuides all show info
    # On the first lookup for a day the information will be loaded from
    # the EPGuides url. This will be saved to local file _epguides_YYYYMMDD.csv
    # and any old files will be removed. Subsequent accesses for the same day will read this file.
    today = datetime.date.today().strftime("%Y%m%d")
    saveFile = '_epguides_' + today + '.csv'
    saveFilePath = os.path.join(self.SAVE_DIR, saveFile)
    if os.path.exists(saveFilePath):
      # Load data previous saved to file
      with open(saveFilePath, 'r') as allShowsFile:
        self._idList = allShowsFile.read()
    else:
      # Download new list from EPGUIDES and strip any leading or trailing whitespace
      self._idList = util.WebLookup(self.ALLSHOW_IDLIST_URL).strip()

      # Save to file to avoid multiple url requests in same day
      with open(saveFilePath, 'w') as allShowsFile:
        allShowsFile.write(self._idList)

      # Delete old copies of this file
      globPattern = '_epguides_????????.csv'
      globFilePath = os.path.join(self.SAVE_DIR, globPattern)
      for filePath in glob.glob(globFilePath):
        if filePath != saveFilePath:
          print('Removing old EPGUIDES file:', filePath)
          os.remove(filePath)

  def _GetShowID(self, showName):
    # Look up EPGuides showID (tvrage) for given showName
    showID = None

    # Populate self._idList if it does not already exist
    if self._idList is None:
      self._GetShowIDList()

    # Read self._idList as csv file
    idReader = csv.reader(self._idList.splitlines())
    titleList = []
    idList = []
    for rowCnt, row in enumerate(idReader):
      if rowCnt == 0:
        # Get header column index
        for colCnt, column in enumerate(row):
          if column == 'title':
            titleIndex = colCnt
          if column == 'tvrage':
            rageIndex = colCnt
      else:
        # Make list of all titles
        titleList.append(row[titleIndex])
        idList.append(row[rageIndex])

    # Get title which has the best match to showName
    ratioMatch = []
    for title in titleList:
      ratioMatch.append(util.GetBestStringMatchValue(showName, title))

    maxRatio = max(ratioMatch)
    matchTitleIndex = [i for i, j in enumerate(ratioMatch) if j == maxRatio]

    if len(matchTitleIndex) == 1:
      index = matchTitleIndex[0]
      showID = idList[index]
    elif len(matchTitleIndex) > 1:
      print("Multiple title with equal match characteristics detected")
      print("Best match titles are:")
      for index in matchTitleIndex:
        print("Title: {0} (ID:{1})".format(titleList[index], idList[index]))

    if showID is None:
      print("An EPGuides ID could not be found for show {0}".format(showName))
    else:
      return(showID)

  def _ExtractDataFromShowHtml(self, html):
    # Extracts show data from <html><body><pre>
    xmlRoot = etree.fromstring(html)
    for child in xmlRoot:
      if child.tag == 'body':
        for subChild in child:
          if subChild.tag =='pre':
            # Return text with leading and trailing whitespace stripped
            return(subChild.text.strip())
    raise Exception("Show content not found - check EPGuides html formatting")

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
        if int(row[seasonIndex]) == int(season) and int(row[episodeIndex]) == int(episode):
          print("Episode name is {0}".format(row[titleIndex]))
          return(row[titleIndex])
    print("No episode name found for S{0}E{1}".format(season, episode))

  def EpisodeLookUp(self, showName, season, episode):
    # Get name of epsiode for given showName, season and epsiode
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
        episodeName = self._GetEpisodeName(showID, season, episode)
        return(episodeName)

