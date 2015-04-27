''' TV File Object '''
# Python default package imports
import os
import re

# Local file imports
import logzila
import util

#################################################
# TVFile
#################################################
class TVFile:
  #################################################
  # constructor
  #################################################
  def __init__(self, filePath):
    self.origFilePath = filePath
    self.origFileName = os.path.splitext(os.path.basename(filePath))[0]
    self.fileDir = os.path.dirname(filePath)
    self.ext = os.path.splitext(filePath)[1]
    self.fileShowName = None
    self.seasonNum = None
    self.episodeNum = None
    self.episodeName = None
    self.guideShowName = None
    self.newFileName = None
    self.newFilePath = None

  ############################################################################
  # GetShowDetails
  # Extract show details from file name
  # Expecting unique season and episode give in form S([0-9]+)E([0-9]+)
  # All information preceeding this is used as the show name
  ############################################################################
  def GetShowDetails(self):
    match = re.findall("[sS]([0-9]+)[eE]([0-9]+)", self.origFileName)
    match = set(match) # Eliminate any duplicate matches

    if len(match) != 1:
      if len(match) == 0:
        logzila.Log.Info("TVFILE", "Incompatible filename no season and episode match detected: {0}".format(self.origFilePath))
      else:
        logzila.Log.Info("TVFILE", "Incompatible filename multiple different season and episode matches detected: {0}".format(self.origFilePath))
      return(False)
    else:
      (self.seasonNum, self.episodeNum) = match.pop()
      if len(self.seasonNum) == 1:
        self.seasonNum = "0{0}".format(self.seasonNum)
      if len(self.episodeNum) == 1:
        self.episodeNum = "0{0}".format(self.episodeNum)
      self.fileShowName = re.findall("(.+?)[_.-?][sS][0-9]+[eE][0-9]+", self.origFileName)[0]
      return(True)

  ############################################################################
  # GenerateNewFileName
  # Create new file name from show name, season number, episode number
  # and episode name.
  ############################################################################
  def GenerateNewFileName(self):
    if self.guideShowName is not None and self.seasonNum is not None and \
       self.episodeNum is not None and self.episodeName is not None:
      newFileName = "{0}.S{1}E{2}.{3}{4}".format(self.guideShowName, self.seasonNum, \
                                            self.episodeNum, self.episodeName, self.ext)
      self.newFileName = util.StripSpecialCharacters(newFileName)

  ############################################################################
  # GenerateNewFilePath
  # Create new file path. If a fileDir is provided it will be used otherwise
  # the original file path is used.
  ############################################################################
  def GenerateNewFilePath(self, fileDir = None):
    self.GenerateNewFileName()
    if self.newFileName is not None:
      if fileDir is None:
        fileDir = self.fileDir
      self.newFilePath = os.path.join(fileDir, self.newFileName)

  ############################################################################
  # Print
  ############################################################################
  def Print(self):
    logzila.Log.Info("TVFILE", "TV File details are:")
    logzila.Log.IncreaseIndent()
    logzila.Log.Info("TVFILE", "Original File Path      = {0}".format(self.origFilePath))
    if self.guideShowName is not None:
      logzila.Log.Info("TVFILE", "Show Name (from guide)  = {0}".format(self.guideShowName))
    elif self.fileShowName is not None:
      logzila.Log.Info("TVFILE", "Show Name (from file)   = {0}".format(self.fileShowName))
    if self.seasonNum is not None and self.episodeNum is not None:
      logzila.Log.Info("TVFILE", "Season & Episode        = S{0}E{1}".format(self.seasonNum, self.episodeNum))
    if self.episodeName is not None:
      logzila.Log.Info("TVFILE", "Episode Name:           = {0}".format(self.episodeName))
    if self.newFilePath is not None:
      logzila.Log.Info("TVFILE", "New File Path           = {0}".format(self.newFilePath))
    logzila.Log.DecreaseIndent()
