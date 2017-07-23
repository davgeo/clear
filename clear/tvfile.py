'''

tvfile.py

Class objects used to store TV file and show information

'''
# Python default package imports
import os
import re
import types

# Third-party package imports
import goodlogging

# Local file imports
import clear.util as util

#################################################
# ShowInfo
#################################################
class ShowInfo:
  """
  Show infomation object.

  Attributes:
    showID : int
      Unique identifier for show

    showName : string
      Show name

    seasonNum : int
      Season number

    episodeNum : int
      Episode number

    episodeName : int
      Episode name

    multiPartEpisodeNumbers : list
      List containing any subsquent episode numbers
      which are also part of this file (e.g. S01_02)
  """

  #################################################
  # constructor
  #################################################
  def __init__(self, showID=None, showName=None, seasonNum=None, episodeNum=None, episodeName=None):
    """
    Constructor. Initialise object values.

    Parameters:
      showID : int [optional: default = None]
      showName : string [optional: default = None]
      seasonNum : int [optional: default = None]
      episodeNum : int [optional: default = None]
      episodeName : int [optional: default = None]
     """
    self.showID = showID
    self.showName = showName
    self.seasonNum = seasonNum
    self.episodeNum = episodeNum
    self.episodeName = episodeName
    self.multiPartEpisodeNumbers = []

  #################################################
  # __lt__
  # define preferred sort order
  #################################################
  def __lt__(self, other):
    """
    Less than comparison of ShowInfo objects.
    If any field is None return False otherwise sort
    by showName, then seasonNum then by episodeNum.

    Parameters:
      other : ShowInfo object
        Object to compare against

    Returns:
      True if this object is less than other,
      otherwise it returns False.
    """
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
  """
  TV file infomation object.

  Attributes:
    fileInfo : types.SimpleNamespace object
      Contains file infomation

    showInfo : ShowInfo object
      Contains show information
  """

  #################################################
  # constructor
  #################################################
  def __init__(self, filePath):
    """
    Constructor. Initialise object values.

    Parameters:
      filePath : string
        Original path to file
    """
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
    """
    Less than comparison of TVFile objects.
    Sort by showInfo value

    Parameters:
      other : TVFile object
        Object to compare against

    Returns:
      True if this object is less than other,
      otherwise it returns False.
    """
    return self.showInfo < other.showInfo

  ############################################################################
  # GetShowDetails
  ############################################################################
  def GetShowDetails(self):
    """
    Extract show name, season number and episode number from file name.

    Supports formats S<NUM>E<NUM> or <NUM>x<NUM> for season and episode numbers
    where letters are case insensitive and number can be one or more digits. It
    expects season number to be unique however it can handle either single or
    multipart episodes (consecutive values only).

    All information preceeding season number is used for the show name lookup. This
    string is forced to lowercase and stripped of special characters

    Parameters:
      N/A

    Returns:
      False if an incompatible file name is found, otherwise return True.
    """

    fileName = os.path.splitext(os.path.basename(self.fileInfo.origPath))[0]

    # Episode Number
    episodeNumSubstring = set(re.findall("(?<=[0-9])[xXeE][0-9]+(?:[xXeE_.-][0-9]+)*", fileName))

    if len(episodeNumSubstring) != 1:
      goodlogging.Log.Info("TVFILE", "Incompatible filename no episode match detected: {0}".format(self.fileInfo.origPath))
      return False

    episodeNumSet = set(re.findall("(?<=[xXeE_.-])[0-9]+", episodeNumSubstring.pop()))

    episodeNumList = [int(i) for i in episodeNumSet]
    episodeNumList.sort()

    episodeNum = "{0}".format(episodeNumList[0])
    if len(episodeNumList) > 1:
      episodeNumReference = episodeNumList[0]
      for episodeNumIter in episodeNumList[1:]:
        if episodeNumIter == (episodeNumReference+1):
          strNum = "{0}".format(episodeNumIter)
          if len(strNum) == 1:
            strNum = "0{0}".format(strNum)

          self.showInfo.multiPartEpisodeNumbers.append(strNum)
          episodeNumReference = episodeNumIter
        else:
          break

    if len(episodeNum) == 1:
      episodeNum = "0{0}".format(episodeNum)

    self.showInfo.episodeNum = episodeNum

    # Season Number
    seasonNumSet = set(re.findall("[sS]([0-9]+)", fileName))
    preceedingS = True

    if len(seasonNumSet) == 1:
      seasonNum = seasonNumSet.pop()
    else:
      seasonNumSet = set(re.findall("([0-9]+)[xX](?:[0-9]+[xX])*", fileName))
      preceedingS = False

      if len(seasonNumSet) == 1:
        seasonNum = seasonNumSet.pop()
      else:
        goodlogging.Log.Info("TVFILE", "Incompatible filename no season match detected: {0}".format(self.fileInfo.origPath))
        return False

    if len(seasonNum) == 1:
      seasonNum = "0{0}".format(seasonNum)

    self.showInfo.seasonNum = seasonNum

    # Show Name
    if preceedingS is True:
      showNameList = re.findall("(.+?)\s*[_.-]*\s*[sS][0-9]+[xXeE][0-9]+.*", fileName)
    else:
      showNameList = re.findall("(.+?)\s*[_.-]*\s*[0-9]+[xXeE][0-9]+.*", fileName)

    if len(showNameList) == 1:
      showName = util.StripSpecialCharacters(showNameList[0].lower(), stripAll=True)
    else:
      goodlogging.Log.Info("TVFILE", "Incompatible filename no show name detected: {0}".format(self.fileInfo.origPath))
      return False

    self.fileInfo.showName = showName
    return True

  ############################################################################
  # GenerateNewFileName
  ############################################################################
  def GenerateNewFileName(self):
    """
    Create new file name from show name, season number, episode number
    and episode name in format ShowName.S<NUM>.E<NUM>.EpisodeName.

    Parameters:
      N/A

    Returns:
      newFileName : string
        New file name in format ShowName.S<NUM>.E<NUM>.EpisodeName.
    """
    if self.showInfo.showName is not None and self.showInfo.seasonNum is not None and \
       self.showInfo.episodeNum is not None and self.showInfo.episodeName is not None:
      ext = os.path.splitext(self.fileInfo.origPath)[1]
      newFileName = "{0}.S{1}E{2}".format(self.showInfo.showName, self.showInfo.seasonNum, \
                                            self.showInfo.episodeNum)

      for episodeNum in self.showInfo.multiPartEpisodeNumbers:
        newFileName = newFileName + "_{0}".format(episodeNum)

      newFileName = newFileName + ".{0}{1}".format(self.showInfo.episodeName, ext)
      newFileName = util.StripSpecialCharacters(newFileName)
      return newFileName

  ############################################################################
  # GenerateNewFilePath
  ############################################################################
  def GenerateNewFilePath(self, fileDir = None):
    """
    Create new file path. If a fileDir is provided it will be used otherwise
    the original file path is used. Updates file info object with new path.

    Parameters:
      fileDir : string [optional : default = None]
        Optional file directory

    Returns:
      N/A
    """
    newFileName = self.GenerateNewFileName()
    if newFileName is not None:
      if fileDir is None:
        fileDir = os.path.dirname(self.fileInfo.origPath)
      self.fileInfo.newPath = os.path.join(fileDir, newFileName)

  ############################################################################
  # Print
  ############################################################################
  def Print(self):
    """ Print contents of showInfo and FileInfo object """
    goodlogging.Log.Info("TVFILE", "TV File details are:")
    goodlogging.Log.IncreaseIndent()
    goodlogging.Log.Info("TVFILE", "Original File Path      = {0}".format(self.fileInfo.origPath))
    if self.showInfo.showName is not None:
      goodlogging.Log.Info("TVFILE", "Show Name (from guide)  = {0}".format(self.showInfo.showName))
    elif self.fileInfo.showName is not None:
      goodlogging.Log.Info("TVFILE", "Show Name (from file)   = {0}".format(self.fileInfo.showName))
    if self.showInfo.seasonNum is not None and self.showInfo.episodeNum is not None:
      goodlogging.Log.Info("TVFILE", "Season & Episode        = S{0}E{1}".format(self.showInfo.seasonNum, self.showInfo.episodeNum))
    if self.showInfo.episodeName is not None:
      goodlogging.Log.Info("TVFILE", "Episode Name:           = {0}".format(self.showInfo.episodeName))
    if self.fileInfo.newPath is not None:
      goodlogging.Log.Info("TVFILE", "New File Path           = {0}".format(self.fileInfo.newPath))
    goodlogging.Log.DecreaseIndent()
