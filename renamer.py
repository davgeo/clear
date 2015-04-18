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
  def __init__(self, tvFileList, guideName = 'EPGUIDES', destDir = None, dbPath = None):
    self._fileList  = tvFileList
    self._targetDir = destDir
    if dbPath is not None:
      self._db        = database.RenamerDB(dbPath)
    self._SetGuide(guideName)

  # *** INTERNAL CLASSES *** #
  ############################################################################
  # _SetGuide
  # Select guide corresponding to guideName
  # Supported: EPGUIDES
  ############################################################################
  def _SetGuide(self, guideName):
    if(guideName == 'EPGUIDES'):
      self._guide = epguides.EPGuidesLookup()
    else:
      raise Exception("Unknown guide set for TVRenamer selection")

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
  # Look up show name from guide. Allows user to accept or decline best match
  # or to provide an alternate match to lookup.
  ############################################################################
  def _GetGuideShowName(self, string):
    # Look up string in guide to find best tv show match
    print("Looking up show name for: {0}".format(string))
    showName = self._db.GetShowName(string)
    showNameList = self._guide.ShowNameLookUp(string)

    showNameListStr = ', '.join(showNameList)

    if len(showNameList) == 1:
      prompt = "  Match found: {0}\n".format(showNameListStr) \
             + "  Enter 'y' to accept show name or e"
    elif len(showNameList) > 1:
      prompt = "  Multiple possible matches found: {0}\n".format(showNameListStr) \
             + "  Enter correct show name from list or e"
    else:
      prompt = "  No match found\n  E"

    prompt = prompt + "nter a different show name to look up or " \
           + "enter 'x' to skip this show: "

    response = input(prompt)

    if response.lower() == 'x':
      return None
    elif response.lower() == 'y' and len(showNameList) == 1:
      return showNameList[0]
    elif len(showNameList) > 1:
      for showName in showNameList:
        if response.lower() == showName.lower():
          return(showName)
    return self._GetGuideShowName(response)

  ############################################################################
  # _RenameFile
  # Renames file
  ############################################################################
  def _RenameFile(self, tvFile):
    processedDir = 'PROCESSED'
    if tvFile.newFilePath is not None:
      print("Copying {0} to {1}".format(tvFile.origFilePath, tvFile.newFilePath))
      # shutil copy

      print("Moving original file {0} to processed dir {1}\n".format(tvFile.origFilePath, processedDir))
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
      showNameMatchDict[fileShowName] = self._db.GetShowName(fileShowName)
      if showNameMatchDict[fileShowName] is None:
        showNameMatchDict[fileShowName] = self._GetGuideShowName(fileShowName)
        if showNameMatchDict[fileShowName] is not None:
          self._db.AddShowName(fileShowName, showNameMatchDict[fileShowName])

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
    print("Renaming files:\n")
    for tvFile in activeFileList:
      tvFile.GenerateNewFilePath(self._targetDir)
      print(tvFile.Convert2String(), "\n")
      self._RenameFile(tvFile)

    print("\n*** -------------------------------- ***")
    print("Skipped files:")
    for tvFile in skippedFileList:
      if tvFile.guideShowName is None:
        print("  {0} (Missing show name)".format(tvFile.origFilePath))
      elif tvFile.episodeName is None:
        print("  {0} (Missing episode name)".format(tvFile.origFilePath))
      elif tvFile.newFilePath is None:
        print("  {0} (Failed to create new file path)".format(tvFile.origFilePath))
      else:
        print("  {0} (Unknown reason)".format(tvFile.origFilePath))


