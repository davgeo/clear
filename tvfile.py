''' TV File Object '''
# Python default package imports
import os
import re
import types

# Local file imports
import logzila
import util

#################################################
# ShowInfo
#################################################
class ShowInfo:
  #################################################
  # constructor
  #################################################
  def __init__(self, showID = None, showName = None):
    self.showID = showID
    self.showName = showName
    self.seasonNum = None
    self.episodeNum = None
    self.episodeName = None

  #################################################
  # __lt__
  # define preferred sort order
  #################################################
  def __lt__(self, other):
    if self.showID is None or other.showID is None:
      return False
    elif self.showID == other.showID:
      if self.seasonNum is None or other.seasonNum is None:
        return False
      elif self.seasonNum == other.seasonNum:
        if self.episodeNum is None or other.episodeNum is None:
          return False
        else:
          return self.episodeNum < other.episodeNum
      else:
        return self.seasonNum < other.seasonNum
    else:
      return self.showName < other.showName

#################################################
# TVFile
#################################################
class TVFile:
  #################################################
  # constructor
  #################################################
  def __init__(self, filePath):
    self.fileInfo = types.SimpleNamespace()
    self.fileInfo.origPath = filePath
    self.fileInfo.newPath = None
    self.fileInfo.showName = None

    self.showInfo = ShowInfo()

  #################################################
  # __lt__
  # define preferred sort order
  #################################################
  def __lt__(self, other):
    return self.showInfo < other.showInfo

  ############################################################################
  # GetShowDetails
  # Extract show details from file name
  # Expecting unique season and episode give in form S([0-9]+)E([0-9]+)
  # All information preceeding this is used as the show name
  ############################################################################
  def GetShowDetails(self):
    fileName = os.path.splitext(os.path.basename(self.fileInfo.origPath))[0]
    match = re.findall("[sS]([0-9]+)[eE]([0-9]+)", fileName)
    match = set(match) # Eliminate any duplicate matches

    if len(match) != 1:
      if len(match) == 0:
        logzila.Log.Info("TVFILE", "Incompatible filename no season and episode match detected: {0}".format(self.fileInfo.origPath))
      else:
        logzila.Log.Info("TVFILE", "Incompatible filename multiple different season and episode matches detected: {0}".format(self.fileInfo.origPath))
      return(False)
    else:
      (self.showInfo.seasonNum, self.showInfo.episodeNum) = match.pop()
      if len(self.showInfo.seasonNum) == 1:
        self.showInfo.seasonNum = "0{0}".format(self.showInfo.seasonNum)
      if len(self.showInfo.episodeNum) == 1:
        self.showInfo.episodeNum = "0{0}".format(self.showInfo.episodeNum)
      self.fileInfo.showName = re.findall("(.+?)[_.-?][sS][0-9]+[eE][0-9]+", fileName)[0]
      return(True)

  ############################################################################
  # GenerateNewFileName
  # Create new file name from show name, season number, episode number
  # and episode name.
  ############################################################################
  def GenerateNewFileName(self):
    if self.showInfo.showName is not None and self.showInfo.seasonNum is not None and \
       self.showInfo.episodeNum is not None and self.showInfo.episodeName is not None:
      ext = os.path.splitext(self.fileInfo.origPath)[1]
      newFileName = "{0}.S{1}E{2}.{3}{4}".format(self.showInfo.showName, self.showInfo.seasonNum, \
                                            self.showInfo.episodeNum, self.showInfo.episodeName, ext)
      newFileName = util.StripSpecialCharacters(newFileName)
      return newFileName

  ############################################################################
  # GenerateNewFilePath
  # Create new file path. If a fileDir is provided it will be used otherwise
  # the original file path is used.
  ############################################################################
  def GenerateNewFilePath(self, fileDir = None):
    newFileName = self.GenerateNewFileName()
    if newFileName is not None:
      if fileDir is None:
        fileDir = os.path.dirname(self.fileInfo.origPath)
      self.fileInfo.newPath = os.path.join(fileDir, newFileName)

  ############################################################################
  # Print
  ############################################################################
  def Print(self):
    logzila.Log.Info("TVFILE", "TV File details are:")
    logzila.Log.IncreaseIndent()
    logzila.Log.Info("TVFILE", "Original File Path      = {0}".format(self.fileInfo.origPath))
    if self.showInfo.showName is not None:
      logzila.Log.Info("TVFILE", "Show Name (from guide)  = {0}".format(self.showInfo.showName))
    elif self.fileInfo.showName is not None:
      logzila.Log.Info("TVFILE", "Show Name (from file)   = {0}".format(self.fileInfo.showName))
    if self.showInfo.seasonNum is not None and self.showInfo.episodeNum is not None:
      logzila.Log.Info("TVFILE", "Season & Episode        = S{0}E{1}".format(self.showInfo.seasonNum, self.showInfo.episodeNum))
    if self.showInfo.episodeName is not None:
      logzila.Log.Info("TVFILE", "Episode Name:           = {0}".format(self.showInfo.episodeName))
    if self.fileInfo.newPath is not None:
      logzila.Log.Info("TVFILE", "New File Path           = {0}".format(self.fileInfo.newPath))
    logzila.Log.DecreaseIndent()
