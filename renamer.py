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
  def __init__(self, db, tvFileList, guideName = epguides.EPGuidesLookup.GUIDE_NAME, destDir = None, inPlaceRename = False, forceCopy = False):
    self._db        = db
    self._fileList  = tvFileList
    self._tvDir = destDir
    self._forceCopy = forceCopy
    self._inPlaceRename = inPlaceRename
    self._SetGuide(guideName)

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
    showNameList = [tvFile.fileInfo.showName for tvFile in tvFileList]
    return(set(showNameList))

  ############################################################################
  # _GetShowID
  # Look up show name from database or guide. Allows user to accept or
  # decline best match or to provide an alternate match to lookup.
  ############################################################################
  def _GetShowID(self, stringSearch, origStringSearch = None):
    showInfo = tvfile.ShowInfo()

    if origStringSearch is None:
      logzila.Log.Info("RENAMER", "Looking up show ID for: {0}".format(stringSearch))
      origStringSearch = stringSearch

    logzila.Log.IncreaseIndent()

    showInfo.showID = self._db.SearchFileNameTable(stringSearch)

    if showInfo.showID is None:
      logzila.Log.Info("RENAMER", "No show ID match found for '{0}' in database".format(stringSearch))
      showNameList = self._guide.ShowNameLookUp(stringSearch)
      showName = util.UserAcceptance(showNameList)

      if showName in showNameList:
        libEntry = self._db.SearchTVLibrary(showName = showName)

        if libEntry is None:
          logzila.Log.Info("RENAMER", "No show by this name found in TV library database. Is this a new show for the database?")
          response = logzila.Log.Input("RENAMER", "Enter 'y' (yes), 'n' (no) or 'ls' (list existing shows): ")
          response = util.ValidUserResponse(response, ('y', 'n', 'ls'))
          if response.lower() == 'ls':
            dbLibList = self._db.SearchTVLibrary()
            if dbLibList is None:
              logzila.Log.Info("RENAMER", "TV library is empty")
              response = 'y'
            else:
              dbShowNameList = [i[1] for i in dbLibList]
              dbShowNameStr = ', '.join(dbShowNameList)
              logzila.Log.Info("RENAMER", "Existing shows in database are: {0}".format(dbShowNameStr))
              response = logzila.Log.Input("RENAMER", "Is this a new show? [y/n]: ")
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
                logzila.Log.Info("RENAMER", "No show ID found - TV library is empty")
                return None
              dbShowNameList = [i[1] for i in dbLibList]
            finally:
              while showInfo.showID is None:
                matchShowList = util.GetBestMatch(showName, dbShowNameList)
                showName = util.UserAcceptance(matchShowList)
                if showName is None:
                  logzila.Log.Info("RENAMER", "No show ID found - could not match to existing show")
                  return None
                elif showName in matchShowList:
                  showInfo.showID = self._db.SearchTVLibrary(showName = showName)[0][0]
                  showInfo.showName = showName

        else:
          showInfo.showID = libEntry[0][0]

        self._db.AddToFileNameTable(origStringSearch, showInfo.showID)

        logzila.Log.DecreaseIndent()
        return showInfo
      elif showName is None:
        logzila.Log.DecreaseIndent()
        return None
      else:
        logzila.Log.DecreaseIndent()
        return self._GetShowID(showName, origStringSearch)
    else:
      logzila.Log.Info("RENAMER", "Match found: show ID = {0}".format(showInfo.showID))
      if origStringSearch != stringSearch:
        self._db.AddToFileNameTable(origStringSearch, showInfo.showID)
      logzila.Log.DecreaseIndent()
      return showInfo

  ############################################################################
  # _GetShowName
  ############################################################################
  def _GetShowInfo(self, stringSearch):
    logzila.Log.Info("RENAMER", "Looking up show info for: {0}".format(stringSearch))
    logzila.Log.IncreaseIndent()
    showInfo = self._GetShowID(stringSearch)
    if showInfo is None:
      logzila.Log.DecreaseIndent()
      return None
    elif showInfo.showID is None:
      logzila.Log.DecreaseIndent()
      return None
    elif showInfo.showName is None:
      showInfo.showName = self._db.SearchTVLibrary(showID = showInfo.showID)[0][1]
      logzila.Log.Info("RENAMER", "Found show name: {0}".format(showInfo.showName))
      logzila.Log.DecreaseIndent()
      return showInfo
    else:
      logzila.Log.DecreaseIndent()
      return showInfo

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

    logzila.Log.Info("RENAMER", "PROCESSING FILE: {0}".format(oldPath))

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
      logzila.Log.Info("RENAMER", "RENAME COMPLETE: {0}".format(newPath))

  ############################################################################
  # _CreateNewSeasonDir
  ############################################################################
  def _CreateNewSeasonDir(self, seasonNum):
    seasonDirName = "Season {0}".format(seasonNum)
    logzila.Log.Info("RENAMER", "Generated directory name: '{0}'".format(seasonDirName))
    response = logzila.Log.Input("RENAMER", "Enter 'y' to accept this directory, 'b' to use base show directory, 'x' to skip this file or enter a new directory name to use: ")
    response = util.CheckEmptyResponse(response)
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
    logzila.Log.Info("RENAMER", "Looking up season directory for show {0}".format(showID))
    logzila.Log.IncreaseIndent()

    # Look up existing season folder from database
    seasonDirName = self._db.SearchSeasonDirTable(showID, seasonNum)

    if seasonDirName is not None:
      logzila.Log.Info("RENAMER", "Found season directory match from database: {0}".format(seasonDirName))
    else:
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
                logzila.Log.Info("RENAMER", "Show directory is empty")
              else:
                logzila.Log.Info("RENAMER", "Show directory contains: {0}".format(', '.join(dirList)))
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

    logzila.Log.DecreaseIndent()
    return seasonDirName

  ############################################################################
  # _CreateNewShowDir
  ############################################################################
  def _CreateNewShowDir(self, showName):
    stripedDir = util.StripSpecialCharacters(showName)
    logzila.Log.Info("RENAMER", "Suggested show directory name is: '{0}'".format(stripedDir))
    response = logzila.Log.Input('RENAMER', "Enter 'y' to accept this directory, 'x' to skip this show or enter a new directory to use: ")
    if response.lower() == 'x':
      return None
    elif response.lower() == 'y':
      return stripedDir
    else:
      return response

  ############################################################################
  # _GenerateLibraryPath
  #
  ############################################################################
  def _GenerateLibraryPath(self, tvFile, libraryDir):
    logzila.Log.Info("RENAMER", "Looking up library directory in database for show: {0}".format(tvFile.showInfo.showName))
    logzila.Log.IncreaseIndent()
    showID, showName, showDir = self._db.SearchTVLibrary(showName = tvFile.showInfo.showName)[0]

    if showDir is None:
      logzila.Log.Info("RENAMER", "No directory match found in database - looking for best match in library directory: {0}".format(libraryDir))
      dirList = os.listdir(libraryDir)
      listDir = False
      matchName = tvFile.showInfo.showName
      while showDir is None:
        if len(dirList) == 0:
          logzila.Log.Info("RENAMER", "TV Library directory is empty")
          response = None
        else:
          if listDir is True:
            logzila.Log.Info("RENAMER", "TV library directory contains: {0}".format(', '.join(dirList)))
          else:
            matchDirList = util.GetBestMatch(matchName, dirList)

          listDirPrompt = "enter 'ls' to list all items in TV library directory"
          response = util.UserAcceptance(matchDirList, promptComment = listDirPrompt, promptOnly = listDir, xStrOverride = "to create new show directory")
          listDir = False

        if response is None:
          showDir = self._CreateNewShowDir(tvFile.showInfo.showName)
          if showDir is None:
            logzila.Log.DecreaseIndent()
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

    logzila.Log.DecreaseIndent()

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
    # ------------------------------------------------------------------------
    # Get list of unique fileInfo show names and find matching actual show
    # names from database or TV guide
    # ------------------------------------------------------------------------
    showNameMatchDict = {}
    uniqueFileShowList = self._GetUniqueFileShowNames(self._fileList)
    if len(uniqueFileShowList) > 0:
      logzila.Log.Seperator()

    for fileShowName in uniqueFileShowList:
      showNameMatchDict[fileShowName] = self._GetShowInfo(fileShowName)
      logzila.Log.NewLine()

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
      logzila.Log.Seperator()

    validEpisodeNameFileList = []

    logzila.Log.Info("RENAMER", "Looking up episode names:\n")

    for tvFile in validShowFileList:
      tvFile.showInfo.episodeName = self._guide.EpisodeNameLookUp(tvFile.showInfo.showName, tvFile.showInfo.seasonNum, tvFile.showInfo.episodeNum)

      if tvFile.showInfo.episodeName is None:
        incompatibleFileList.append(tvFile)
      else:
        validEpisodeNameFileList.append(tvFile)

      logzila.Log.Info("RENAMER", "{0} S{1}E{2}: {3}".format(tvFile.showInfo.showName, tvFile.showInfo.seasonNum, tvFile.showInfo.episodeNum, tvFile.showInfo.episodeName))

    logzila.Log.NewLine()

    # ------------------------------------------------------------------------
    # Print file details and generate new file paths
    # ------------------------------------------------------------------------
    logzila.Log.Seperator()

    renameFileList = []
    skippedFileList = []

    logzila.Log.Info("RENAMER", "Generating library paths:\n")

    if len(validEpisodeNameFileList) == 0:
      logzila.Log.Info("RENAMER", "No compatible files were detected")
    else:
      for tvFile in validEpisodeNameFileList:
        tvFile.Print()
        logzila.Log.NewLine()
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

        logzila.Log.NewLine()

      # ------------------------------------------------------------------------
      # Rename files
      # ------------------------------------------------------------------------
      logzila.Log.Seperator()

      logzila.Log.Info("RENAMER", "Renamable files:\n")

      if len(renameFileList) == 0:
        logzila.Log.Info("RENAMER", "No renamable files were detected")
      else:
        showName = None
        renameFileList.sort()

        for tvFile in renameFileList:
          if showName is None or showName != tvFile.showInfo.showName:
            showName = tvFile.showInfo.showName
            logzila.Log.Info("RENAMER", "{0}".format(showName))
          logzila.Log.IncreaseIndent()
          logzila.Log.Info("RENAMER", "FROM: {0}".format(tvFile.fileInfo.origPath))
          logzila.Log.Info("RENAMER", "TO:   {0}".format(tvFile.fileInfo.newPath))
          logzila.Log.DecreaseIndent()
          logzila.Log.NewLine()

        response = logzila.Log.Input('RENAMER', "***WARNING*** CONTINUE WITH RENAME PROCESS? [y/n]: ")
        response = util.ValidUserResponse(response, ('y','n'))

        if response == 'n':
          logzila.Log.Info("RENAMER", "Renaming process skipped")
        else:
          logzila.Log.NewLine()
          if self._inPlaceRename is False:
            logzila.Log.Info("RENAMER", "Adding files to TV library:\n")
          else:
            logzila.Log.Info("RENAMER", "Renaming files:\n")
          for tvFile in renameFileList:
            self._MoveFileToLibrary(tvFile.fileInfo.origPath, tvFile.fileInfo.newPath)
            logzila.Log.NewLine()

    # ------------------------------------------------------------------------
    # List skipped files
    # ------------------------------------------------------------------------
    if len(skippedFileList) > 0:
      logzila.Log.Seperator()
      logzila.Log.Info("RENAMER", "Skipped files:")
      logzila.Log.IncreaseIndent()
      for tvFile in skippedFileList:
        if tvFile.fileInfo.origPath == tvFile.fileInfo.newPath:
          logzila.Log.Info("RENAMER", "{0} (No rename required)".format(tvFile.fileInfo.origPath))
        else:
          logzila.Log.Info("RENAMER", "{0} (Unknown reason)".format(tvFile.fileInfo.origPath))
      logzila.Log.DecreaseIndent()

    # ------------------------------------------------------------------------
    # List incompatible files
    # ------------------------------------------------------------------------
    if len(incompatibleFileList) > 0:
      logzila.Log.Seperator()
      logzila.Log.Info("RENAMER", "Incompatible files:")
      logzila.Log.IncreaseIndent()
      for tvFile in incompatibleFileList:
        if tvFile.showInfo.showName is None:
          logzila.Log.Info("RENAMER", "{0} (Missing show name)".format(tvFile.fileInfo.origPath))
        elif tvFile.showInfo.episodeName is None:
          logzila.Log.Info("RENAMER", "{0} (Missing episode name)".format(tvFile.fileInfo.origPath))
        elif tvFile.fileInfo.newPath is None:
          logzila.Log.Info("RENAMER", "{0} (Failed to create new file path)".format(tvFile.fileInfo.origPath))
        else:
          logzila.Log.Info("RENAMER", "{0} (Unknown reason)".format(tvFile.fileInfo.origPath))
      logzila.Log.DecreaseIndent()

