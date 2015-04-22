''' RENAMER '''
# Python default package imports
import shutil

# Custom Python package imports

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
  def __init__(self, db, tvFileList, guideName = epguides.EPGuidesLookup.GUIDE_NAME, destDir = None):
    self._db        = db
    self._fileList  = tvFileList
    self._tvDir = destDir
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

    logzila.Log.DecreaseIndent()

    if showName in showNameList:
      self._db.AddShowName(self._guide.GUIDE_NAME, origStringSearch, showName)
      return showName
    elif showName is None:
      return None
    else:
      return self._GetGuideShowName(showName, origStringSearch)

  ############################################################################
  # _RenameFile
  # Renames file
  ############################################################################
  def _RenameFile(self, tvFile):
    processedDir = 'PROCESSED'
    if tvFile.newFilePath is not None:
      logzila.Log.Info("RENAMER", "Copying {0} to {1}".format(tvFile.origFilePath, tvFile.newFilePath))
      # shutil copy

      logzila.Log.Info("RENAMER", "Moving original file {0} to processed dir {1}\n".format(tvFile.origFilePath, processedDir))
      #shutil.move(tvFile.origFilePath, tvFile.newFilePath)

  ############################################################################
  # _AddFileToLibrary
  #
  ############################################################################
  def _AddFileToLibrary(self, tvFile):
    # Look up base show name directory in database
    showDir = self._db.GetLibraryDirectory()

    # Parse TV dir for best match
    libraryDir = self._tvDir # possibly db lookup here instead of in dm.py
    dirList = os.path.listdir(libraryDir)
    while showDir is None:
      matchDirList = util.GetBestMatch(tvFile.guideShowName, dirList)

      # User input to accept or add alternate
      response = util.UserAcceptance(matchDirList)

      if response in matchDirList:
        showDir = response
      elif response is None:
        return None

    # Generate file directory path
    #showDir = re.sub('[!@#$%^&*(){};:,./<>?\|`~=_+]', '', self.guideShowName)
    #showDir = re.sub('\s\s+', ' ', showDir)
    #fileDir = os.path.join(fileDir, showDir, "Season {0}".format(self.seasonNum))
    # Call tvFile function to generate file name

    # Rename file

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
          tvFile.GenerateNewFilePath(self._tvDir)
          if tvFile.newFilePath is None:
            skippedFileList.append(tvFile)
          else:
            activeFileList.append(tvFile)
      else:
        skippedFileList.append(tvFile)

    logzila.Log.Seperator()
    logzila.Log.Info("RENAMER", "Renaming files:\n")
    for tvFile in activeFileList:
      tvFile.Print()
      self._RenameFile(tvFile)

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


