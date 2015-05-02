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
    # Returns a list containing all unique show names entires from tvFileList
    showNameList = [tvFile.fileShowName for tvFile in tvFileList]
    return(set(showNameList))

  ############################################################################
  # _GetGuideShowName
  # Look up show name from database or guide. Allows user to accept or
  # decline best match or to provide an alternate match to lookup.
  ############################################################################
  def _GetGuideShowName(self, stringSearch, origStringSearch = None):
    if origStringSearch is None:
      logzila.Log.Info("RENAMER", "Looking up show name for: {0}".format(stringSearch))
      origStringSearch = stringSearch

    logzila.Log.IncreaseIndent()

    showName = self._db.GetShowName(self._guide.GUIDE_NAME, stringSearch)

    if showName is not None:
      if origStringSearch != stringSearch:
        self._db.AddShowName(self._guide.GUIDE_NAME, origStringSearch, showName)
      logzila.Log.DecreaseIndent()
      return showName

    showNameList = self._guide.ShowNameLookUp(stringSearch)

    showName = util.UserAcceptance(showNameList)

    if showName in showNameList:
      self._db.AddShowName(self._guide.GUIDE_NAME, origStringSearch, showName)
      logzila.Log.DecreaseIndent()
      return showName
    elif showName is None:
      logzila.Log.DecreaseIndent()
      return None
    else:
      logzila.Log.DecreaseIndent()
      return self._GetGuideShowName(showName, origStringSearch)

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
  # _LookUpSeasonDirectory
  ############################################################################
  def _LookUpSeasonDirectory(self, showDir, seasonNum):
    logzila.Log.Info("RENAMER", "Looking up season directory (Season {0}) in {1}".format(seasonNum, showDir))

    #TODO: Add database lookup

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

    # User input to accept or add alternate
    response = util.UserAcceptance(matchDirList, recursiveLookup = False)

    if response in matchDirList:
      seasonDirName = response
    elif response is None:
      seasonDirName = "Season {0}".format(seasonNum)
      logzila.Log.Info("RENAMER", "Generated directory name: '{0}'".format(seasonDirName))
      response = logzila.Log.Input("RENAMER", "Enter 'y' to accept this directory, 'x' to use base show directory or enter a new directory name to use: ")
      if response.lower() == 'x':
        seasonDirName = None
      elif response.lower() == 'y':
        pass
      else:
        seasonDirName = response

    # TODO: Add seasonDirName to Database

    if seasonDirName is not None:
      showDir = os.path.join(showDir, seasonDirName)

    return showDir

  ############################################################################
  # _AddFileToLibrary
  #
  ############################################################################
  def _AddFileToLibrary(self, tvFile):
    # Look up base show name directory in database
    logzila.Log.Info("RENAMER", "Looking up library directory in database for show: {0}".format(tvFile.guideShowName))
    showDir = self._db.GetLibraryDirectory(tvFile.guideShowName)

    if showDir is None:
      logzila.Log.Info("RENAMER", "No database match found - look for best match in library directory: {0}".format(self._tvDir))
      # Parse TV dir for best match
      libraryDir = self._tvDir # TODO: possibly db lookup here instead of in dm.py
      dirList = os.listdir(libraryDir)
      while showDir is None:
        matchDirList = util.GetBestMatch(tvFile.guideShowName, dirList)

        # User input to accept or add alternate
        response = util.UserAcceptance(matchDirList)

        if response in matchDirList:
          showDir = response
        elif response is None:
          stripedDir = util.StripSpecialCharacters(tvFile.guideShowName)
          response = logzila.Log.Input('RENAMER', "Enter 'y' to accept this directory, 'x' to skip this show or enter a new directory to use: ")
          if response.lower() == 'x':
            return None
          elif response.lower() == 'y':
            showDir = stripedDir
          else:
            showDir = response

      self._db.AddLibraryDirectory(tvFile.guideShowName, showDir)

    # Add base directory to show path
    showDir = os.path.join(self._tvDir, showDir)

    # Lookup and add season directory to show path
    showDir = self._LookUpSeasonDirectory(showDir, tvFile.seasonNum)

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
      showNameMatchDict[fileShowName] = self._GetGuideShowName(fileShowName)

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

    logzila.Log.Seperator()
    logzila.Log.Info("RENAMER", "Renaming files:\n")
    for tvFile in activeFileList:
      tvFile.Print()
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


