'''

renamer.py

TV episode renamer

'''
# Python default package imports
import shutil
import os
import re
import errno

# Third-party package imports
import goodlogging

# Local file imports
import clear.epguides as epguides
import clear.tvfile as tvfile
import clear.database as database
import clear.util as util

#################################################
# TVRenamer
#################################################
class TVRenamer:
  """
  TV renamer class. The run method of this class
  implements the main job flow for renaming all
  TV files from a given file list.

  Attributes:
    This class has no public attributes.

    These attributes are used internally:
      _db : RenamerDB object
        Object used for database access.

      _fileList : list
        List of tvfile.TVFile objects to rename.

      _archiveDir : string
        Directory to move archived file to.

      _tvDir : string
        Root directory for renamed TV files.

      _forceCopy : boolean
        Enables copying of files if target directory
        is on a different file system.

      _inPlaceRename : boolean
        If set do renaming in the current directory.
        Do not use the tvDir directory.

      _skipUserInput : boolean
        If set skip any user inputs. If a single option
        is available this will be selected otherwise no
        further action will be taken.

      _guide : EPGuidesLookup object
        Object for doing lookups from web TV guide.
  """

  #################################################
  # constructor
  #################################################
  def __init__(self, db, tvFileList, archiveDir, guideName = epguides.EPGuidesLookup.GUIDE_NAME, tvDir = None, inPlaceRename = False, forceCopy = False, skipUserInput = False):
    """
    Constructor. Initialise object values.

    Parameters:
      db : RenamerDB object
        Object used for database access.

      tvFileList : list
        List of tvfile.TVFile objects.

      archiveDir : string
        Directory to move archived file to.

      guideName : string [optional: default = epguides.EPGuidesLookup.GUIDE_NAME]
        Name of guide to use (e.g. EPGUIDES)

      tvDir : string [optional: default = None]
        Root directory for renamed TV files.

      inPlaceRename : boolean [optional: default = False]
        If set do renaming in the current directory.
        Do not use the tvDir directory.

      forceCopy : boolean [optional: default = False]
        Enables copying of files if target directory
        is on a different file system.

      skipUserInput : boolean [optional: default = False]
        If set skip any user inputs. If a single option
        is available this will be selected otherwise no
        further action will be taken.
     """
    self._db            = db
    self._fileList      = tvFileList
    self._archiveDir    = archiveDir
    self._tvDir         = tvDir
    self._forceCopy     = forceCopy
    self._inPlaceRename = inPlaceRename
    self._skipUserInput = skipUserInput
    self._SetGuide(guideName)

  # *** INTERNAL CLASSES *** #
  ############################################################################
  # _SetGuide
  ############################################################################
  def _SetGuide(self, guideName):
    """
    Select guide corresponding to guideName

    Supported: EPGUIDES

    Parameters:
      guideName : string
        Name of guide to use.
    """
    if(guideName == epguides.EPGuidesLookup.GUIDE_NAME):
      self._guide = epguides.EPGuidesLookup()
    else:
      raise Exception("[RENAMER] Unknown guide set for TVRenamer selection: Got {}, Expected {}".format(guideName, epguides.EPGuidesLookup.GUIDE_NAME))

  ############################################################################
  # _GetUniqueFileShowNames
  ############################################################################
  def _GetUniqueFileShowNames(self, tvFileList):
    """
    Return a list containing all unique show names from tvfile.TVFile object
    list.

    Parameters:
      tvFileList : list
        List of tvfile.TVFile objects.

    Returns:
      The set of show names from the tvfile.TVFile list.
    """
    showNameList = [tvFile.fileInfo.showName for tvFile in tvFileList]
    return(set(showNameList))

  ############################################################################
  # _GetShowID
  ############################################################################
  def _GetShowID(self, stringSearch, origStringSearch = None):
    """
    Search for given string as an existing entry in the database file name
    table or, if no match is found, as a show name from the TV guide.

    If an exact match is not found in the database the user can accept
    or decline the best match from the TV guide or can provide an alternate
    match to lookup.

    Parameters:
      stringSearch : string
        String to look up in database or guide.

      origStringSearch : string [optional: default = None]
        Original search string, used by recusive function calls.

    Returns:
      If no show id could be found this returns None, otherwise
      it returns a tvfile.ShowInfo object containing show name
      and show id.
    """
    showInfo = tvfile.ShowInfo()

    if origStringSearch is None:
      goodlogging.Log.Info("RENAMER", "Looking up show ID for: {0}".format(stringSearch))
      origStringSearch = stringSearch

    goodlogging.Log.IncreaseIndent()

    showInfo.showID = self._db.SearchFileNameTable(stringSearch)

    if showInfo.showID is None:
      goodlogging.Log.Info("RENAMER", "No show ID match found for '{0}' in database".format(stringSearch))
      showNameList = self._guide.ShowNameLookUp(stringSearch)

      if self._skipUserInput is True:
        if len(showNameList) == 1:
          showName = showNameList[0]
          goodlogging.Log.Info("RENAMER", "Automatic selection of showname: {0}".format(showName))
        else:
          showName = None
          goodlogging.Log.Info("RENAMER", "Show skipped - could not make automatic selection of showname")
      else:
        showName = util.UserAcceptance(showNameList)

      if showName in showNameList:
        libEntry = self._db.SearchTVLibrary(showName = showName)

        if libEntry is None:
          if self._skipUserInput is True:
            response = 'y'
          else:
            goodlogging.Log.Info("RENAMER", "No show by this name found in TV library database. Is this a new show for the database?")
            response = goodlogging.Log.Input("RENAMER", "Enter 'y' (yes), 'n' (no) or 'ls' (list existing shows): ")
            response = util.ValidUserResponse(response, ('y', 'n', 'ls'))

            if response.lower() == 'ls':
              dbLibList = self._db.SearchTVLibrary()
              if dbLibList is None:
                goodlogging.Log.Info("RENAMER", "TV library is empty")
                response = 'y'
              else:
                dbShowNameList = [i[1] for i in dbLibList]
                dbShowNameStr = ', '.join(dbShowNameList)
                goodlogging.Log.Info("RENAMER", "Existing shows in database are: {0}".format(dbShowNameStr))
                response = goodlogging.Log.Input("RENAMER", "Is this a new show? [y/n]: ")
                response = util.ValidUserResponse(response, ('y', 'n'))
          if response.lower() == 'y':
            showInfo.showID = self._db.AddShowToTVLibrary(showName)
            showInfo.showName = showName
          else:
            try:
              dbShowNameList
            except NameError:
              dbLibList = self._db.SearchTVLibrary()
              if dbLibList is None:
                goodlogging.Log.Info("RENAMER", "No show ID found - TV library is empty")
                return None
              dbShowNameList = [i[1] for i in dbLibList]

            while showInfo.showID is None:
              matchShowList = util.GetBestMatch(showName, dbShowNameList)
              showName = util.UserAcceptance(matchShowList)
              if showName is None:
                goodlogging.Log.Info("RENAMER", "No show ID found - could not match to existing show")
                return None
              elif showName in matchShowList:
                showInfo.showID = self._db.SearchTVLibrary(showName = showName)[0][0]
                showInfo.showName = showName

        else:
          showInfo.showID = libEntry[0][0]

        self._db.AddToFileNameTable(origStringSearch, showInfo.showID)

        goodlogging.Log.DecreaseIndent()
        return showInfo
      elif showName is None:
        goodlogging.Log.DecreaseIndent()
        return None
      else:
        goodlogging.Log.DecreaseIndent()
        return self._GetShowID(showName, origStringSearch)
    else:
      goodlogging.Log.Info("RENAMER", "Match found: show ID = {0}".format(showInfo.showID))
      if origStringSearch != stringSearch:
        self._db.AddToFileNameTable(origStringSearch, showInfo.showID)
      goodlogging.Log.DecreaseIndent()
      return showInfo

  ############################################################################
  # _GetShowInfo
  ############################################################################
  def _GetShowInfo(self, stringSearch):
    """
    Calls GetShowID and does post processing checks on result.

    Parameters:
      stringSearch : string
        String to look up in database or guide.

    Returns:
      If GetShowID returns None or if it returns showInfo with showID = None
      then this will return None, otherwise it will return the showInfo object.
    """
    goodlogging.Log.Info("RENAMER", "Looking up show info for: {0}".format(stringSearch))
    goodlogging.Log.IncreaseIndent()
    showInfo = self._GetShowID(stringSearch)
    if showInfo is None:
      goodlogging.Log.DecreaseIndent()
      return None
    elif showInfo.showID is None:
      goodlogging.Log.DecreaseIndent()
      return None
    elif showInfo.showName is None:
      showInfo.showName = self._db.SearchTVLibrary(showID = showInfo.showID)[0][1]
      goodlogging.Log.Info("RENAMER", "Found show name: {0}".format(showInfo.showName))
      goodlogging.Log.DecreaseIndent()
      return showInfo
    else:
      goodlogging.Log.DecreaseIndent()
      return showInfo

  ############################################################################
  # _MoveFileToTVLibrary
  ############################################################################
  def _MoveFileToLibrary(self, oldPath, newPath):
    """
    Move file from old file path to new file path. This follows certain
    conditions:

      If file already exists at destination do rename inplace.

      If file destination is on same file system and doesn't exist rename and
      move.

      If source and destination are on different file systems do rename in-place,
        and if forceCopy is true copy to dest and move orig to archive directory.

    Parameters:
      oldPath : string
        Old file path.

      newPath : string
        New file path.

    Returns:
      If old and new file paths are the same or if the new file path already exists
      this returns False. If file rename is skipped for any reason this returns None
      otherwise if rename completes okay it returns True.
    """
    if oldPath == newPath:
      return False

    goodlogging.Log.Info("RENAMER", "PROCESSING FILE: {0}".format(oldPath))

    if os.path.exists(newPath):
      goodlogging.Log.Info("RENAMER", "File skipped - file aleady exists in TV library at {0}".format(newPath))
      return False

    newDir = os.path.dirname(newPath)
    os.makedirs(newDir, exist_ok=True)

    try:
      os.rename(oldPath, newPath)
    except OSError as ex:
      if ex.errno is errno.EXDEV:
        goodlogging.Log.Info("RENAMER", "Simple rename failed - source and destination exist on different file systems")
        goodlogging.Log.Info("RENAMER", "Renaming file in-place")
        newFileName = os.path.basename(newPath)
        origFileDir = os.path.dirname(oldPath)
        renameFilePath = os.path.join(origFileDir, newFileName)
        if oldPath != renameFilePath:
          renameFilePath = util.CheckPathExists(renameFilePath)
          goodlogging.Log.Info("RENAMER", "Renaming from {0} to {1}".format(oldPath, renameFilePath))
        else:
          goodlogging.Log.Info("RENAMER", "File already has the correct name ({0})".format(newFileName))

        try:
          os.rename(oldPath, renameFilePath)
        except Exception as ex2:
          goodlogging.Log.Info("RENAMER", "File rename skipped - Exception ({0}): {1}".format(ex2.args[0], ex2.args[1]))
        else:
          if self._forceCopy is True:
            goodlogging.Log.Info("RENAMER", "Copying file to new file system {0} to {1}".format(renameFilePath, newPath))

            try:
              shutil.copy2(renameFilePath, newPath)
            except shutil.Error as ex3:
              err = ex3.args[0]
              goodlogging.Log.Info("RENAMER", "File copy failed - Shutil Error: {0}".format(err))
            else:
              util.ArchiveProcessedFile(renameFilePath, self._archiveDir)
              return True
          else:
            goodlogging.Log.Info("RENAMER", "File copy skipped - copying between file systems is disabled (enabling this functionality is slow)")
      else:
        goodlogging.Log.Info("RENAMER", "File rename skipped - Exception ({0}): {1}".format(ex.args[0], ex.args[1]))
    except Exception as ex:
      goodlogging.Log.Info("RENAMER", "File rename skipped - Exception ({0}): {1}".format(ex.args[0], ex.args[1]))
    else:
      goodlogging.Log.Info("RENAMER", "RENAME COMPLETE: {0}".format(newPath))
      return True

  ############################################################################
  # _CreateNewSeasonDir
  ############################################################################
  def _CreateNewSeasonDir(self, seasonNum):
    """
    Creates a new season directory name in the form 'Season <NUM>'.

    If skipUserInput is True this will be accepted by default otherwise the
    user can choose to accept this, use the base show directory or enter
    a different name.

    Parameters:
      seasonNum : int
        Season number

    Returns:
      If the user accepts the generated directory name or gives a new name
      this will be returned. If it the user chooses to use the base
      directory an empty string is returned. If the user chooses to skip at
      this input stage None is returned.
    """
    seasonDirName = "Season {0}".format(seasonNum)
    goodlogging.Log.Info("RENAMER", "Generated directory name: '{0}'".format(seasonDirName))

    if self._skipUserInput is False:
      response = goodlogging.Log.Input("RENAMER", "Enter 'y' to accept this directory, 'b' to use base show directory, 'x' to skip this file or enter a new directory name to use: ")
      response = util.CheckEmptyResponse(response)
    else:
      response = 'y'

    if response.lower() == 'b':
      return ''
    elif response.lower() == 'y':
      return seasonDirName
    elif response.lower() == 'x':
      return None
    else:
      return response

  ############################################################################
  # _LookUpSeasonDirectory
  ############################################################################
  def _LookUpSeasonDirectory(self, showID, showDir, seasonNum):
    """
    Look up season directory. First attempt to find match from database,
    otherwise search TV show directory. If no match is found in the database
    the user can choose to accept a match from the TV show directory, enter
    a new directory name to use or accept an autogenerated name.

    Parameters:
      showID : int
        Show ID number

      showDir : string
        Path to show file directory

      seasonNum : int
        Season number

    Returns:
      seasonDirName : string
        Name of season directory to use. This can be a blank string to
        use the root show directory, an autogenerated string or a user
        given string.
    """
    goodlogging.Log.Info("RENAMER", "Looking up season directory for show {0}".format(showID))
    goodlogging.Log.IncreaseIndent()

    # Look up existing season folder from database
    seasonDirName = self._db.SearchSeasonDirTable(showID, seasonNum)

    if seasonDirName is not None:
      goodlogging.Log.Info("RENAMER", "Found season directory match from database: {0}".format(seasonDirName))
    else:
      # Look up existing season folder in show directory
      goodlogging.Log.Info("RENAMER", "Looking up season directory (Season {0}) in {1}".format(seasonNum, showDir))
      if os.path.isdir(showDir) is False:
        goodlogging.Log.Info("RENAMER", "Show directory ({0}) is not an existing directory".format(showDir))
        seasonDirName = self._CreateNewSeasonDir(seasonNum)
      else:
        matchDirList = []
        for dirName in os.listdir(showDir):
          subDir = os.path.join(showDir, dirName)
          if os.path.isdir(subDir):
            seasonResult = re.findall("Season", dirName)
            if len(seasonResult) > 0:
              numResult = re.findall("[0-9]+", dirName)
              numResult = set(numResult)
              if len(numResult) == 1:
                if int(numResult.pop()) == int(seasonNum):
                  matchDirList.append(dirName)

        if self._skipUserInput is True:
          if len(matchDirList) == 1:
            userAcceptance = matchDirList[0]
            goodlogging.Log.Info("RENAMER", "Automatic selection of season directory: {0}".format(seasonDirName))
          else:
            userAcceptance = None
            goodlogging.Log.Info("RENAMER", "Could not make automatic selection of season directory")
        else:
          listDirPrompt = "enter 'ls' to list all items in show directory"
          userAcceptance = util.UserAcceptance(matchDirList, promptComment = listDirPrompt, xStrOverride = "to create new season directory")

        if userAcceptance in matchDirList:
          seasonDirName = userAcceptance
        elif userAcceptance is None:
          seasonDirName = self._CreateNewSeasonDir(seasonNum)
        else:
          recursiveSelectionComplete = False
          promptOnly = False
          dirLookup = userAcceptance
          while recursiveSelectionComplete is False:
            dirList = os.listdir(showDir)
            if dirLookup.lower() == 'ls':
              dirLookup = ''
              promptOnly = True
              if len(dirList) == 0:
                goodlogging.Log.Info("RENAMER", "Show directory is empty")
              else:
                goodlogging.Log.Info("RENAMER", "Show directory contains: {0}".format(', '.join(dirList)))
            else:
              matchDirList = util.GetBestMatch(dirLookup, dirList)
              response = util.UserAcceptance(matchDirList, promptComment = listDirPrompt, promptOnly = promptOnly, xStrOverride = "to create new season directory")
              promptOnly = False

              if response in matchDirList:
                seasonDirName = response
                recursiveSelectionComplete = True
              elif response is None:
                seasonDirName = self._CreateNewSeasonDir(seasonNum)
                recursiveSelectionComplete = True
              else:
                dirLookup = response

      # Add season directory to database
      if seasonDirName is not None:
        self._db.AddSeasonDirTable(showID, seasonNum, seasonDirName)

    goodlogging.Log.DecreaseIndent()
    return seasonDirName

  ############################################################################
  # _CreateNewShowDir
  ############################################################################
  def _CreateNewShowDir(self, showName):
    """
    Create new directory name for show. An autogenerated choice, which is the
    showName input that has been stripped of special characters, is proposed
    which the user can accept or they can enter a new name to use. If the
    skipUserInput variable is True the autogenerated value is accepted
    by default.

    Parameters:
      showName : string
        Name of TV show

    Returns:
      Either the autogenerated directory name, the user given directory name
      or None if the user chooses to skip at this input stage.
    """
    stripedDir = util.StripSpecialCharacters(showName)
    goodlogging.Log.Info("RENAMER", "Suggested show directory name is: '{0}'".format(stripedDir))

    if self._skipUserInput is False:
      response = goodlogging.Log.Input('RENAMER', "Enter 'y' to accept this directory, 'x' to skip this show or enter a new directory to use: ")
    else:
      response = 'y'

    if response.lower() == 'x':
      return None
    elif response.lower() == 'y':
      return stripedDir
    else:
      return response

  ############################################################################
  # _GenerateLibraryPath
  ############################################################################
  def _GenerateLibraryPath(self, tvFile, libraryDir):
    """
    Creates a full path for TV file in TV library.

    This initially attempts to directly match a show directory in the database,
    if this fails it searches the library directory for the best match. The
    user can then select an existing match or can propose a new directory to
    use as the show root directory.

    The season directory is also generated and added to the show and
    library directories. This is then used by the tvFile GenerateNewFilePath
    method to create a new path for the file.

    Parameters:
      tvFile : tvfile.TVFile object
        Contains show and file info.

      libraryDir : string
        Root path of TV library directory.

    Returns:
      tvFile : tvFile.TVFile object
        This is an updated version of the input object.
    """
    goodlogging.Log.Info("RENAMER", "Looking up library directory in database for show: {0}".format(tvFile.showInfo.showName))
    goodlogging.Log.IncreaseIndent()
    showID, showName, showDir = self._db.SearchTVLibrary(showName = tvFile.showInfo.showName)[0]

    if showDir is None:
      goodlogging.Log.Info("RENAMER", "No directory match found in database - looking for best match in library directory: {0}".format(libraryDir))
      dirList = os.listdir(libraryDir)
      listDir = False
      matchName = tvFile.showInfo.showName
      while showDir is None:
        if len(dirList) == 0:
          goodlogging.Log.Info("RENAMER", "TV Library directory is empty")
          response = None
        else:
          if listDir is True:
            goodlogging.Log.Info("RENAMER", "TV library directory contains: {0}".format(', '.join(dirList)))
          else:
            matchDirList = util.GetBestMatch(matchName, dirList)

          listDir = False

          if self._skipUserInput is True:
            if len(matchDirList) == 1:
              response = matchDirList[0]
              goodlogging.Log.Info("RENAMER", "Automatic selection of show directory: {0}".format(response))
            else:
              response = None
              goodlogging.Log.Info("RENAMER", "Could not make automatic selection of show directory")
          else:
            listDirPrompt = "enter 'ls' to list all items in TV library directory"
            response = util.UserAcceptance(matchDirList, promptComment = listDirPrompt, promptOnly = listDir, xStrOverride = "to create new show directory")

        if response is None:
          showDir = self._CreateNewShowDir(tvFile.showInfo.showName)
          if showDir is None:
            goodlogging.Log.DecreaseIndent()
            return tvFile
        elif response.lower() == 'ls':
          listDir = True
        elif response in matchDirList:
          showDir = response
        else:
          matchName = response

      self._db.UpdateShowDirInTVLibrary(showID, showDir)

    # Add base directory to show path
    showDir = os.path.join(libraryDir, showDir)

    goodlogging.Log.DecreaseIndent()

    # Lookup and add season directory to show path
    seasonDir = self._LookUpSeasonDirectory(showID, showDir, tvFile.showInfo.seasonNum)

    if seasonDir is None:
      return tvFile
    else:
      showDir = os.path.join(showDir, seasonDir)

    # Call tvFile function to generate file name
    tvFile.GenerateNewFilePath(showDir)

    return tvFile

  # *** EXTERNAL CLASSES *** #
  ############################################################################
  # Run
  ############################################################################
  def Run(self):
    """
    Renames all TV files from the constructor given file list.

    It follows a number of key steps:

      1) Extract a list of unique show titles from file name and lookup
         actual show names from database or TV guide.
      2) Update each file with showID and showName.
      3) Get episode name for all remaining files in valid list.
      4) Print file details and generate new file paths.
      5) Rename files.
      6) List skipped and incompatible files.

    Parameters:
      N/A

    Returns:
      N/A
    """
    # ------------------------------------------------------------------------
    # Get list of unique fileInfo show names and find matching actual show
    # names from database or TV guide
    # ------------------------------------------------------------------------
    showNameMatchDict = {}
    uniqueFileShowList = self._GetUniqueFileShowNames(self._fileList)
    if len(uniqueFileShowList) > 0:
      goodlogging.Log.Seperator()

    for fileShowName in uniqueFileShowList:
      showNameMatchDict[fileShowName] = self._GetShowInfo(fileShowName)
      goodlogging.Log.NewLine()

    # ------------------------------------------------------------------------
    # Update each file with showID and showName
    # ------------------------------------------------------------------------
    incompatibleFileList = []
    validShowFileList = []

    for tvFile in self._fileList:
      if showNameMatchDict[tvFile.fileInfo.showName] is None:
        incompatibleFileList.append(tvFile)
      else:
        tvFile.showInfo.showID = showNameMatchDict[tvFile.fileInfo.showName].showID
        tvFile.showInfo.showName = showNameMatchDict[tvFile.fileInfo.showName].showName
        validShowFileList.append(tvFile)

    # ------------------------------------------------------------------------
    # Get episode name for all remaining files in valid list
    # ------------------------------------------------------------------------
    if len(validShowFileList) > 0:
      goodlogging.Log.Seperator()

    validEpisodeNameFileList = []

    goodlogging.Log.Info("RENAMER", "Looking up episode names:\n")

    for tvFile in validShowFileList:
      tvFile.showInfo.episodeName = self._guide.EpisodeNameLookUp(tvFile.showInfo.showName, tvFile.showInfo.seasonNum, tvFile.showInfo.episodeNum)

      if tvFile.showInfo.episodeName is None:
        incompatibleFileList.append(tvFile)
      else:
        validEpisodeNameFileList.append(tvFile)

      goodlogging.Log.Info("RENAMER", "{0} S{1}E{2}: {3}".format(tvFile.showInfo.showName, tvFile.showInfo.seasonNum, tvFile.showInfo.episodeNum, tvFile.showInfo.episodeName))

    goodlogging.Log.NewLine()

    # ------------------------------------------------------------------------
    # Print file details and generate new file paths
    # ------------------------------------------------------------------------
    goodlogging.Log.Seperator()

    renameFileList = []
    skippedFileList = []

    goodlogging.Log.Info("RENAMER", "Generating library paths:\n")

    if len(validEpisodeNameFileList) == 0:
      goodlogging.Log.Info("RENAMER", "No compatible files were detected")
    else:
      for tvFile in validEpisodeNameFileList:
        tvFile.Print()
        goodlogging.Log.NewLine()
        if self._inPlaceRename is False:
          tvFile = self._GenerateLibraryPath(tvFile, self._tvDir)
        else:
          tvFile.GenerateNewFilePath()

        if tvFile.fileInfo.newPath is None:
          incompatibleFileList.append(tvFile)
        elif tvFile.fileInfo.origPath != tvFile.fileInfo.newPath:
          renameFileList.append(tvFile)
        else:
          skippedFileList.append(tvFile)

        goodlogging.Log.NewLine()

      # ------------------------------------------------------------------------
      # Rename files
      # ------------------------------------------------------------------------
      goodlogging.Log.Seperator()

      goodlogging.Log.Info("RENAMER", "Renamable files:\n")

      if len(renameFileList) == 0:
        goodlogging.Log.Info("RENAMER", "No renamable files were detected")
      else:
        showName = None
        renameFileList.sort()

        for tvFile in renameFileList:
          if showName is None or showName != tvFile.showInfo.showName:
            showName = tvFile.showInfo.showName
            goodlogging.Log.Info("RENAMER", "{0}".format(showName))
          goodlogging.Log.IncreaseIndent()
          goodlogging.Log.Info("RENAMER", "FROM: {0}".format(tvFile.fileInfo.origPath))
          goodlogging.Log.Info("RENAMER", "TO:   {0}".format(tvFile.fileInfo.newPath))
          goodlogging.Log.DecreaseIndent()
          goodlogging.Log.NewLine()

        if self._skipUserInput is False:
          response = goodlogging.Log.Input('RENAMER', "***WARNING*** CONTINUE WITH RENAME PROCESS? [y/n]: ")
          response = util.ValidUserResponse(response, ('y','n'))
        else:
          response = 'y'

        if response == 'n':
          goodlogging.Log.Info("RENAMER", "Renaming process skipped")
        elif response == 'y':
          goodlogging.Log.NewLine()
          if self._inPlaceRename is False:
            goodlogging.Log.Info("RENAMER", "Adding files to TV library:\n")
          else:
            goodlogging.Log.Info("RENAMER", "Renaming files:\n")
          for tvFile in renameFileList:
            self._MoveFileToLibrary(tvFile.fileInfo.origPath, tvFile.fileInfo.newPath)
            goodlogging.Log.NewLine()

    # ------------------------------------------------------------------------
    # List skipped files
    # ------------------------------------------------------------------------
    if len(skippedFileList) > 0:
      goodlogging.Log.Seperator()
      goodlogging.Log.Info("RENAMER", "Skipped files:")
      goodlogging.Log.IncreaseIndent()
      for tvFile in skippedFileList:
        if tvFile.fileInfo.origPath == tvFile.fileInfo.newPath:
          goodlogging.Log.Info("RENAMER", "{0} (No rename required)".format(tvFile.fileInfo.origPath))
        else:
          goodlogging.Log.Info("RENAMER", "{0} (Unknown reason)".format(tvFile.fileInfo.origPath))
      goodlogging.Log.DecreaseIndent()

    # ------------------------------------------------------------------------
    # List incompatible files
    # ------------------------------------------------------------------------
    if len(incompatibleFileList) > 0:
      goodlogging.Log.Seperator()
      goodlogging.Log.Info("RENAMER", "Incompatible files:")
      goodlogging.Log.IncreaseIndent()
      for tvFile in incompatibleFileList:
        if tvFile.showInfo.showName is None:
          goodlogging.Log.Info("RENAMER", "{0} (Missing show name)".format(tvFile.fileInfo.origPath))
        elif tvFile.showInfo.episodeName is None:
          goodlogging.Log.Info("RENAMER", "{0} (Missing episode name)".format(tvFile.fileInfo.origPath))
        elif tvFile.fileInfo.newPath is None:
          goodlogging.Log.Info("RENAMER", "{0} (Failed to create new file path)".format(tvFile.fileInfo.origPath))
        else:
          goodlogging.Log.Info("RENAMER", "{0} (Unknown reason)".format(tvFile.fileInfo.origPath))
      goodlogging.Log.DecreaseIndent()

