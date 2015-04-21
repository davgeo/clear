''' TV File Object '''
# Python default package imports
import os
import re

# Local file imports
import logzila

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
    self.newFilePath = None

  ############################################################################
  # GetShowDetails
  # Extract show details from file name
  # Expecting unique season and episode give in form S([0-9]+)E([0-9]+)
  # All information preceeding this is used as the show name
  ############################################################################
  def GetShowDetails(self):
    match = re.findall("S([0-9]+)E([0-9]+)", self.origFileName)
    match = set(match) # Eliminate any duplicate matches

    if len(match) != 1:
      if len(match) == 0:
        logzila.Log.Info("TVFILE", "Incompatible filename no season and episode match detected: {0}".format(self.origFilePath))
      else:
        logzila.Log.Info("TVFILE", "Incompatible filename multiple different season and episode matches detected: {0}".format(self.origFilePath))
      return(False)
    else:
      (self.seasonNum, self.episodeNum) = match.pop()
      self.fileShowName = re.findall("(.+?)[_.-?]S[0-9]+E[0-9]+", self.origFileName)[0]
      return(True)

  ############################################################################
  # GenerateNewFilePath
  # Create new file path from show name, season number, episode number
  # and episode name. If a fileDir is provided it will also be used otherwise
  # the original file path is used.
  ############################################################################
  def GenerateNewFilePath(self, fileDir = None):
    if self.guideShowName is not None and self.seasonNum is not None and \
       self.episodeNum is not None and self.episodeName is not None:
      if fileDir is None:
        fileDir = self.fileDir
      newFileName = "{0}.S{1}E{2}.{3}{4}".format(self.guideShowName, self.seasonNum, \
                                            self.episodeNum, self.episodeName, self.ext)
      self.newFilePath = os.path.join(fileDir, newFileName)

  ############################################################################
  # Convert2String
  ############################################################################
  def Convert2String(self):
    c2s = "TV File details are:" \
                + "\n  Original File Path      = {0}".format(self.origFilePath)

    # Display show name from guide (preferred) or file if present
    if self.guideShowName is not None:
      c2s = c2s + "\n  Show Name (from guide)  = {0}".format(self.guideShowName)
    elif self.fileShowName is not None:
      c2s = c2s + "\n  Show Name (from file)   = {0}".format(self.fileShowName)

    if self.seasonNum is not None and self.episodeNum is not None:
      c2s = c2s + "\n  Season & Episode        = S{0}E{1}".format(self.seasonNum, self.episodeNum)
    if self.episodeName is not None:
      c2s = c2s + "\n  Episode Name:           = {0}".format(self.episodeName)
    if self.newFilePath is not None:
      c2s = c2s + "\n  New File Path           = {0}".format(self.newFilePath)
    return(c2s)

