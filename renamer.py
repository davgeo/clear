''' RENAMER '''
# Python default package imports
import shutil
import os
import re
import errno

# Local file imports
import epguides
import tvfile
import database
import logzila
import util

#################################################
# TVRenamer
#################################################
class TVRenamer:
  #################################################
  # constructor
  #################################################
  def __init__(self, db, tvFileList, guideName = epguides.EPGuidesLookup.GUIDE_NAME, destDir = None, forceCopy = False):
    self._db        = db
    self._fileList  = tvFileList
    self._tvDir = destDir
    self._SetGuide(guideName)
    self._forceCopy = forceCopy

  # *** INTERNAL CLASSES *** #
  ############################################################################
  # _SetGuide
  # Select guide corresponding to guideName
  # Supported: EPGUIDES
  ############################################################################
  def _SetGuide(self, guideName):
    if(guideName == epguides.EPGuidesLookup.GUIDE_NAME):
      self._guide = epguides.EPGuidesLookup()
    else:
      raise Exception("[RENAMER] Unknown guide set for TVRenamer selection")

  ############################################################################
  # _GetUniqueFileShowNames
  # Return a list containing all unique show names from tvFile list
  ############################################################################
  def _GetUniqueFileShowNames(self, tvFileList):
    showNameList = [tvFile.fileShowName for tvFile in tvFileList]
    return(set(showNameList))

  ############################################################################
  # _GetShowID
  # Look up show name from database or guide. Allows user to accept or
  # decline best match or to provide an alternate match to lookup.
  ############################################################################
  def _GetShowID(self, stringSearch, origStringSearch = None):
    if origStringSearch is None:
      logzila.Log.Info("RENAMER", "Looking up show ID for: {0}".format(stringSearch))
      origStringSearch = stringSearch

    logzila.Log.IncreaseIndent()

    showID = self._db.SearchFileNameTable(stringSearch)

    if showID is None:
      logzila.Log.Info("RENAMER", "No show ID match found for '{0}' in database".format(stringSearch))
      showNameList = self._guide.ShowNameLookUp(stringSearch)
      showName = util.UserAcceptance(showNameList)

      if showName in showNameList:
        libEntry = self._db.SearchTVLibrary(showName = showName)

        if libEntry is None:
          response = logzila.Log.Input("RENAMER", "No show by this name found in TV library. Is this a new show? [y/n]: ")
          response = util.ValidUserResponse(response, ('y', 'n'))
          if response.lower() == 'y':
            showID = self._db.AddShowToTVLibrary(showName)
          else:
            dbLibList = self._db.SearchTVLibrary()
            if dbLibList is None:
              logzila.Log.Info("RENAMER", "No show ID found - TV library is empty")
              return None
            dbShowNameList = [i[1] for i in dbLibList]
            while showID is None:
              matchShowList = util.GetBestMatch(showName, dbShowNameList)
              showName = util.UserAcceptance(matchShowList)
              if showName is None:
                logzila.Log.Info("RENAMER", "No show ID found - could not match to existing show")
                return None
              elif showName in matchShowList:
                showID = self._db.SearchTVLibrary(showName = showName)[0][0]
        else:
          showID = libEntry[0][0]

        self._db.AddToFileNameTable(origStringSearch, showID)

        logzila.Log.DecreaseIndent()
        return showID
      elif showName is None:
        logzila.Log.DecreaseIndent()
        return None
      else:
        logzila.Log.DecreaseIndent()
        return self._GetShowID(showName, origStringSearch)
    else:
      logzila.Log.Info("RENAMER", "Match found: show ID = {0}".format(showID))
      if origStringSearch != stringSearch:
        self._db.AddToFileNameTable(origStringSearch, showID)
      logzila.Log.DecreaseIndent()
      return showID

  ############################################################################
  # _GetShowName
  ############################################################################
  def _GetShowName(self, stringSearch):
    logzila.Log.Info("RENAMER", "Looking up show name for: {0}".format(stringSearch))
    logzila.Log.IncreaseIndent()
    showID = self._GetShowID(stringSearch)
    if showID is None:
      return None
    showName = self._db.SearchTVLibrary(showID = showID)[0][1]
    logzila.Log.Info("RENAMER", "Found show name: {0}".format(showName))
    logzila.Log.DecreaseIndent()
    return showName

  ############################################################################
  # _MoveFileToTVLibrary
  # If file already exists at dest - rename inplace
  # Else if file on same file system and doesn't exist - rename
  # Else if src/dst on different file systems
  #    - rename in-place
  #    - copy to dest (if forceCopy is True)
  #    - move orig to PROCESSED
  ############################################################################
  def _MoveFileToLibrary(self, oldPath, newPath):
    if oldPath == newPath:
      return False

    logzila.Log.Info("RENAMER", "Attempting to add file to TV library (from {0} to {1})".format(oldPath, newPath))

    if os.path.exists(newPath):
      logzila.Log.Info("RENAMER", "File skipped - file aleady exists in TV library at {0}".format(newPath))
      return False

    newDir = os.path.dirname(newPath)
    os.makedirs(newDir, exist_ok=True)

    try:
      os.rename(oldPath, newPath)
    except OSError as ex:
      if ex.errno is errno.EXDEV:
        logzila.Log.Info("RENAMER", "Simple rename failed - source and destination exist on different file systems")
        logzila.Log.Info("RENAMER", "Renaming file in-place")
        newFileName = os.path.basename(newPath)
        origFileDir = os.path.dirname(oldPath)
        renameFilePath = os.path.join(origFileDir, newFileName)
        if oldPath != renameFilePath:
          renameFilePath = util.CheckPathExists(renameFilePath)
          logzila.Log.Info("RENAMER", "Renaming from {0} to {1}".format(oldPath, renameFilePath))
        else:
          logzila.Log.Info("RENAMER", "File already has the correct name ({0})".format(newFileName))

        try:
          os.rename(oldPath, renameFilePath)
        except Exception as ex2:
          logzila.Log.Info("RENAMER", "File rename skipped - Exception ({0}): {1}".format(ex2.args[0], ex2.args[1]))
        else:
          if self._forceCopy is True:
            logzila.Log.Info("RENAMER", "Copying file to new file system {0} to {1}".format(renameFilePath, newPath))

            try:
              shutil.copy2(renameFilePath, newPath)
            except shutil.Error as ex3:
              err = ex3.args[0]
              logzila.Log.Info("RENAMER", "File copy failed - Shutil Error: {0}".format(err))
            else:
              logzila.Log.Info("RENAMER", "Moving original file to PROCESSED directory")
              processedDir = os.path.join(origFileDir, 'PROCESSED')
              os.makedirs(processedDir, exist_ok=True)

              try:
                shutil.move(renameFilePath, processedDir)
              except shutil.Error as ex4:
                err = ex4.args[0]
                logzila.Log.Info("RENAMER", "Move to PROCESSED directory failed - Shutil Error: {0}".format(err))
          else:
            logzila.Log.Info("RENAMER", "File copy skipped - copying between file systems is disabled (enabling this functionality is slow)")
      else:
        logzila.Log.Info("RENAMER", "File rename skipped - Exception ({0}): {1}".format(ex.args[0], ex.args[1]))
    except Exception as ex:
      logzila.Log.Info("RENAMER", "File rename skipped - Exception ({0}): {1}".format(ex.args[0], ex.args[1]))
    else:
      logzila.Log.Info("RENAMER", "File renamed from {0} to {1}".format(oldPath, newPath))

  ############################################################################
  # _CreateNewSeasonDir
  ############################################################################
  def _CreateNewSeasonDir(self, seasonNum):
    seasonDirName = "Season {0}".format(seasonNum)
    logzila.Log.Info("RENAMER", "Generated directory name: '{0}'".format(seasonDirName))
    response = logzila.Log.Input("RENAMER", "Enter 'y' to accept this directory, 'x' to use base show directory or enter a new directory name to use: ")
    if response.lower() == 'x':
      return None
    elif response.lower() == 'y':
      return seasonDirName
    else:
      return response

  ############################################################################
  # _LookUpSeasonDirectory
  ############################################################################
  def _LookUpSeasonDirectory(self, showID, showDir, seasonNum):
    logzila.Log.Info("RENAMER", "Looking up season directory for show {0}".format(showID))
    logzila.Log.IncreaseIndent()

    # Look up existing season folder from database
    seasonDirName = self._db.SearchSeasonDirTable(showID, seasonNum)

    if seasonDirName is not None:
      if os.path.isdir(os.path.join(showDir, seasonDirName)):
        logzila.Log.Info("RENAMER", "Found season directory match from database: {0}".format(seasonDirName))
      else:
        logzila.Log.Info("RENAMER", "Season directory match from database ({0}) could not be found in show directory ({1})".format(seasonDirName, showDir))
        seasonDirName = None

    if seasonDirName is None:
      # Look up existing season folder in show directory
      logzila.Log.Info("RENAMER", "Looking up season directory (Season {0}) in {1}".format(seasonNum, showDir))
      if os.path.isdir(showDir) is False:
        logzila.Log.Info("RENAMER", "Show directory ({0}) is not an existing directory".format(showDir))
        seasonDirName = self._CreateNewSeasonDir(seasonNum)
      else:
        matchDirList = []
        if os.path.isdir(showDir):
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

        listDirPrompt = "enter 'ls' to list all items in show directory"
        userAcceptance = util.UserAcceptance(matchDirList, promptComment = listDirPrompt)

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
                logzila.Log.Info("RENAMER", "Show directory is empty")
              else:
                logzila.Log.Info("RENAMER", "Show directory contains: {0}".format(', '.join(dirList)))
            else:
              matchDirList = util.GetBestMatch(dirLookup, dirList)
              response = util.UserAcceptance(matchDirList, promptComment = listDirPrompt, promptOnly = promptOnly)
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
      self._db.AddSeasonDirTable(showID, seasonNum, seasonDirName)

    logzila.Log.DecreaseIndent()
    return seasonDirName

  ############################################################################
  # _AddFileToLibrary
  #
  ############################################################################
  def _AddFileToLibrary(self, tvFile):
    # Look up base show name directory in database
    logzila.Log.Info("RENAMER", "Looking up library directory in database for show: {0}".format(tvFile.guideShowName))
    logzila.Log.IncreaseIndent()
    showID, showName, showDir = self._db.SearchTVLibrary(showName = tvFile.guideShowName)[0]

    if showDir is None:
      logzila.Log.Info("RENAMER", "No directory match found in database - looking for best match in library directory: {0}".format(self._tvDir))
      # Parse TV dir for best match
      libraryDir = self._tvDir # TODO: possibly db lookup here instead of in dm.py
      dirList = os.listdir(libraryDir)
      promptOnly = False
      while showDir is None:
        matchDirList = util.GetBestMatch(tvFile.guideShowName, dirList)

        if len(dirList) == 0:
          logzila.Log.Info("RENAMER", "TV Library directory is empty")
          response = None
        else:
          # User input to accept or add alternate
          listDirPrompt = "enter 'ls' to list all items in TV library directory"
          response = util.UserAcceptance(matchDirList, promptComment = listDirPrompt, promptOnly = promptOnly)
          promptOnly = False

        if response in matchDirList:
          showDir = response
        elif response is None:
          stripedDir = util.StripSpecialCharacters(tvFile.guideShowName)
          response = logzila.Log.Input('RENAMER', "Enter 'y' to accept this directory, 'x' to skip this show or enter a new directory to use: ")
          if response.lower() == 'x':
            logzila.Log.DecreaseIndent()
            return None
          elif response.lower() == 'y':
            showDir = stripedDir
          else:
            showDir = response
        elif response.lower() == 'ls':
          promptOnly = True
          if len(dirList) == 0:
            logzila.Log.Info("RENAMER", "TV library directory is empty")
          else:
            logzila.Log.Info("RENAMER", "TV library directory contains: {0}".format(', '.join(dirList)))

      self._db.UpdateShowDirInTVLibrary(showID, showDir)

    # Add base directory to show path
    showDir = os.path.join(self._tvDir, showDir)

    logzila.Log.DecreaseIndent()

    # Lookup and add season directory to show path
    seasonDir = self._LookUpSeasonDirectory(showID, showDir, tvFile.seasonNum)

    if seasonDir is not None:
      showDir = os.path.join(showDir, seasonDir)

    # Call tvFile function to generate file name
    tvFile.GenerateNewFilePath(showDir)

    # Rename file
    self._MoveFileToLibrary(tvFile.origFilePath, tvFile.newFilePath)


  # *** EXTERNAL CLASSES *** #
  ############################################################################
  # Run
  # Main TVRename flow:
  #  - Get unique file show names
  #  - Get actual show name & corresponding IDs
  #  - Get episode names
  #  - Generate new file paths
  #  - Rename files
  ############################################################################
  def Run(self):
    showNameMatchDict = {}
    uniqueFileShowList = self._GetUniqueFileShowNames(self._fileList)
    logzila.Log.Seperator()
    for fileShowName in uniqueFileShowList:
      showNameMatchDict[fileShowName] = self._GetShowName(fileShowName)
      logzila.Log.NewLine()

    skippedFileList = []
    activeFileList = []
    logzila.Log.Seperator()
    for tvFile in self._fileList:
      tvFile.guideShowName = showNameMatchDict[tvFile.fileShowName]
      if tvFile.guideShowName is not None:
        tvFile.episodeName = self._guide.EpisodeNameLookUp(tvFile.guideShowName, tvFile.seasonNum, tvFile.episodeNum)
        if tvFile.episodeName is None:
          skippedFileList.append(tvFile)
        else:
          activeFileList.append(tvFile)
      else:
        skippedFileList.append(tvFile)
      logzila.Log.NewLine()

    logzila.Log.Seperator()
    logzila.Log.Info("RENAMER", "Renaming files:\n")
    for tvFile in activeFileList:
      tvFile.Print()
      logzila.Log.NewLine()
      self._AddFileToLibrary(tvFile)
      logzila.Log.NewLine()

    logzila.Log.Seperator()
    logzila.Log.Info("RENAMER", "Skipped files:")
    logzila.Log.IncreaseIndent()
    for tvFile in skippedFileList:
      if tvFile.guideShowName is None:
        logzila.Log.Info("RENAMER", "{0} (Missing show name)".format(tvFile.origFilePath))
      elif tvFile.episodeName is None:
        logzila.Log.Info("RENAMER", "{0} (Missing episode name)".format(tvFile.origFilePath))
      elif tvFile.newFilePath is None:
        logzila.Log.Info("RENAMER", "{0} (Failed to create new file path)".format(tvFile.origFilePath))
      else:
        logzila.Log.Info("RENAMER", "{0} (Unknown reason)".format(tvFile.origFilePath))
    logzila.Log.DecreaseIndent()


