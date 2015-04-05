''' EPGUIDES '''
# Python default package imports
import os
import glob
import csv
import datetime

# Custom Python package imports
import requests

class EPGuidesLookup:
  ALLSHOW_IDLIST_URL = 'http://epguides.com/common/allshows.txt'
  EPISODE_LOOKUP_URL = 'http://epguides.com/common/exportToCSV.asp'
  SAVE_DIR = '/Users/Slinc/Work/dm/test_dir'

  def __init__(self):
    self._idList = None
    self._showInfoDict = {}

  def GetShowIDList(self):
    today = datetime.date.today().strftime("%Y%m%d")
    saveFile = '_epguides_' + today + '.csv'
    saveFilePath = os.path.join(self.SAVE_DIR, saveFile)
    if os.path.exists(saveFilePath):
      # Load data previous saved to file
      with open(saveFilePath, 'r') as allShowsFile:
        self._idList = allShowsFile.read()
    else:
      # Download new list from EPGUIDES
      response = requests.get(self.ALLSHOW_IDLIST_URL)
      if(response.status_code == requests.codes.ok):
        self._idList = response.text

        # Save to file to avoid multiple url requests in same day
        with open(saveFilePath, 'w') as allShowsFile:
          allShowsFile.write(self._idList)

        # Delete old copies of this file
        globPattern = '_epguides_????????.csv'
        globFilePath = os.path.join(SAVE_DIR, globPattern)
        for filePath in glob.glob(globFilePath):
          if filePath != saveFilePath:
            print('Removing old EPGUIDES file:', filePath)
            os.remove(filePath)
      else:
        response.raise_for_status()

  def GetShowID(self, showName):
    if self._idList is None:
      self.GetShowIDList()
    return(19267)

  def EpisodeLookUp(self, showName, season, episode):
    print("Looking up episode name for {0} S{1}E{2}".format(showName, season, episode))
    showID = self.GetShowID(showName)
    try:
      self._showInfoDict[showID]
    except KeyError:
      print("Looking up info for new show: {0}({1})".format(showName, showID))
      urlQuery = {'rage': showID}
      response = requests.get(self.EPISODE_LOOKUP_URL, params=urlQuery)
      if(response.status_code == requests.codes.ok):
        self._showInfoDict[showID] = response.text
      else:
        response.raise_for_status()
    else:
      print("Reusing show info previous obtained for: {0}({1})".format(showName, showID))
    finally:
      pass

