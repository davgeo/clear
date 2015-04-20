''' RENAMER '''
# Python default package imports
import shutil

# Custom Python package imports

# Local file imports
import epguides
import tvfile
import database

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
    self._targetDir = destDir
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
      print("[RENAMER] Looking up show name for: {0}".format(stringSearch))
      origStringSearch = stringSearch

    showName = self._db.GetShowName(self._guide.GUIDE_NAME, stringSearch)

    if showName is not None:
      if origStringSearch != stringSearch:
        self._db.AddShowName(self._guide.GUIDE_NAME, origStringSearch, showName)
      return showName

    showNameList = self._guide.ShowNameLookUp(stringSearch)

    showNameListStr = ', '.join(showNameList)

    if len(showNameList) == 1:
      print("  [RENAMER] Match found: {0}".format(showNameListStr))
      prompt = "  [RENAMER] Enter 'y' to accept show name or e"
    elif len(showNameList) > 1:
      print("  [RENAMER] Multiple possible matches found: {0}".format(showNameListStr))
      prompt = "  [RENAMER] Enter correct show name from list or e"
    else:
      print("  [RENAMER] No match found")
      prompt = "  [RENAMER] E"

    prompt = prompt + "nter a different show name to look up or " \
           + "enter 'x' to skip this show: "

    response = input(prompt)

    if response.lower() == 'x':
      return None
    elif response.lower() == 'y' and len(showNameList) == 1:
      self._db.AddShowName(self._guide.GUIDE_NAME, origStringSearch, showNameList[0])
      return showNameList[0]
    elif len(showNameList) > 1:
      for showName in showNameList:
        if response.lower() == showName.lower():
          self._db.AddShowName(self._guide.GUIDE_NAME, origStringSearch, showName)
          return(showName)
    return self._GetGuideShowName(response, origStringSearch)

  ############################################################################
  # _RenameFile
  # Renames file
  ############################################################################
  def _RenameFile(self, tvFile):
    processedDir = 'PROCESSED'
    if tvFile.newFilePath is not None:
      print("[RENAMER] Copying {0} to {1}".format(tvFile.origFilePath, tvFile.newFilePath))
      # shutil copy

      print("[RENAMER] Moving original file {0} to processed dir {1}\n".format(tvFile.origFilePath, processedDir))
      #shutil.move(tvFile.origFilePath, tvFile.newFilePath)

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
    #print(uniqueFileShowList)
    print("\n*** -------------------------------- ***")
    for fileShowName in uniqueFileShowList:
      showNameMatchDict[fileShowName] = self._GetGuideShowName(fileShowName)

    skippedFileList = []
    activeFileList = []
    print("\n*** -------------------------------- ***")
    for tvFile in self._fileList:
      tvFile.guideShowName = showNameMatchDict[tvFile.fileShowName]
      if tvFile.guideShowName is not None:
        tvFile.episodeName = self._guide.EpisodeNameLookUp(tvFile.guideShowName, tvFile.seasonNum, tvFile.episodeNum)
        if tvFile.episodeName is None:
          skippedFileList.append(tvFile)
        else:
          tvFile.GenerateNewFilePath(self._targetDir)
          if tvFile.newFilePath is None:
            skippedFileList.append(tvFile)
          else:
            activeFileList.append(tvFile)
      else:
        skippedFileList.append(tvFile)

    print("\n*** -------------------------------- ***")
    print("[RENAMER] Renaming files:\n")
    for tvFile in activeFileList:
      tvFile.GenerateNewFilePath(self._targetDir)
      print(tvFile.Convert2String(), "\n")
      self._RenameFile(tvFile)

    print("\n*** -------------------------------- ***")
    print("[RENAMER] Skipped files:")
    for tvFile in skippedFileList:
      if tvFile.guideShowName is None:
        print("  [RENAMER] {0} (Missing show name)".format(tvFile.origFilePath))
      elif tvFile.episodeName is None:
        print("  [RENAMER] {0} (Missing episode name)".format(tvFile.origFilePath))
      elif tvFile.newFilePath is None:
        print("  [RENAMER] {0} (Failed to create new file path)".format(tvFile.origFilePath))
      else:
        print("  [RENAMER] {0} (Unknown reason)".format(tvFile.origFilePath))


