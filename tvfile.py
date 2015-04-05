''' TV File Object '''
# Python default package imports
import os
import re

class TVFile:
  def __init__(self, filePath):
    self.origFilePath = filePath
    self.origFileName = os.path.splitext(os.path.basename(filePath))[0]
    self.fileDir = os.path.dirname(filePath)
    self.ext = os.path.splitext(filePath)[1]
    self.showName = None
    self.seasonNum = None
    self.episodeNum = None
    self.episodeName = None
    self.newFilePath = None

  def GetShowDetails(self):
    match = re.findall("S([0-9]+)E([0-9]+)", self.origFileName)
    match = set(match) # Eliminate any duplicate matches

    if len(match) != 1:
      if len(match) == 0:
        print("Incompatible filename no season and episode match detected: {0}".format(self.origFilePath))
      else:
        print("Incompatible filename multiple different season and episode matches detected: {0}".format(self.origFilePath))
      return(False)
    else:
      (self.seasonNum, self.episodeNum) = match.pop()
      self.showName = re.findall("(.+?)[_.-?]S[0-9]+E[0-9]+", self.origFileName)[0]
      return(True)

  def UpdateEpisodeName(self, episodeName):
    self.episodeName = episodeName

  def GenerateNewFilePath(self, fileDir = None):
    if self.showName is not None and self.seasonNum is not None and \
       self.episodeNum is not None and self.episodeName is not None:
      if fileDir is None:
        fileDir = self.fileDir
      newFileName = "{0}.S{1}E{2}.{3}.{4}".format(self.showName, self.seasonNum, \
                                            self.episodeNum, self.episodeName, self.ext)
      self.newFilePath = os.path.join(fileDir, newFileName)

  def Convert2String(self):
    c2s = "TV File details are:\n" \
        + "  Original File Path = {0}\n".format(self.origFilePath) \
        + "  Original File Name = {0}\n".format(self.origFileName) \
        + "  File Dir           = {0}\n".format(self.fileDir) \
        + "  Ext                = {0}".format(self.ext)
    if self.showName is not None:
      c2s = c2s + "\n  Show Name          = {0}".format(self.showName)
    if self.seasonNum is not None and self.episodeNum is not None:
      c2s = c2s + "\n    Season {0} Episode {1}".format(self.seasonNum, self.episodeNum)
    if self.newFilePath is not None:
      c2s = c2s + "\n  New File Path      = {0}".format(self.newFilePath)
    return(c2s)

