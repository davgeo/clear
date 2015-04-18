''' RENAMER '''
# Python default package imports
import shutil

# Custom Python package imports

# Local file imports
import epguides
import tvfile

class TVRenamer:
  #################################################
  # constructor
  #################################################
  def __init__(self, tvFileList, guideName = 'EPGUIDES', destDir = None):
    self._fileList = tvFileList
    self._targetDir = destDir
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
  # _RenameFiles
  # Renames files
  ############################################################################
  def _RenameFiles(self):
    print("Renaming files...")
    for tvFile in self._fileList:
      if tvFile.newFilePath is not None:
        print("Moving {0} to {1}".format(tvFile.origFilePath, tvFile.newFilePath))
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
        if tvFile.episodeName == None:
          skippedFileList.append(tvFile)
        else:
          activeFileList.append(tvFile)
      else:
        skippedFileList.append(tvFile)

    print("\n*** -------------------------------- ***")
    print("Active files:\n")
    for tvFile in activeFileList:
      print(tvFile.Convert2String(), "\n")

    print("\n*** -------------------------------- ***")
    print("Skipped files:")
    for tvFile in skippedFileList:
      if tvFile.guideShowName == None:
        print("  {0} (Missing show name)".format(tvFile.origFilePath))
      elif tvFile.episodeName == None:
        print("  {0} (Missing episode name)".format(tvFile.origFilePath))
      else:
        print("  {0} (Unknown reason)".format(tvFile.origFilePath))
    #self.RenameFiles(tvFileList)


