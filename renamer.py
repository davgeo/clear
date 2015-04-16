''' RENAMER '''
# Python default package imports
import shutil

# Custom Python package imports

# Local file imports
import epguides
import tvfile

class TVRenamer:
  def __init__(self, tvFileList, guideName = 'EPGUIDES', destDir = None):
    self._fileList = tvFileList
    self._targetDir = destDir
    self._SetGuide(guideName)

  def _SetGuide(self, guideName):
    if(guideName == 'EPGUIDES'):
      self._guide = epguides.EPGuidesLookup()
    else:
      raise Exception("Unknown guide set for TVRenamer selection")

  def _GetUniqueFileShowNames(self, tvFileList):
    # Returns a list containing all unique show names entires from tvFileList
    showNameList = [tvFile.showName for tvFile in tvFileList]
    return(set(showNameList))

  def GenerateNewFileInfo(self):
    for tvFile in self._fileList:
      print("\n*** -------------------------------- ***")
      episodeName = self._guide.EpisodeLookUp(tvFile.showName, tvFile.seasonNum, tvFile.episodeNum)
      tvFile.UpdateEpisodeName(episodeName)
      tvFile.GenerateNewFilePath(self._targetDir)
      print(tvFile.Convert2String())
      #raise Exception("TEST END")

  def RenameFiles(self):
    print("Renaming files...")
    for tvFile in self._fileList:
      if tvFile.newFilePath is not None:
        print("Moving {0} to {1}".format(tvFile.origFilePath, tvFile.newFilePath))
        #shutil.move(tvFile.origFilePath, tvFile.newFilePath)

  def _GetGuideShowName(self, string):
    # Look up string in guide to find best tv show match
    print("\n*** -------------------------------- ***")
    print("Looking up show name for {0}".format(string))
    showName = self._guide.ShowNameLookUp(string)

    if len(showName) == 1:
      prompt = "Match found: {0}\n".format(showName) \
             + "Enter 'y' to accept show name or\n"
    elif len(showName) > 1:
      prompt = "Multiple possible matches found {0}".format(showName) \
             + "Enter correct show name from list or\n"
    else:
      prompt = "No match found\n"

    prompt = prompt + "Enter a different show name to look up or\n" \
           + "Enter 'x' to skip this show: "

    response = input(prompt)

    if(response == 'y'):
      return showName
    elif(response == 'x'):
      return None
    else:
      return self._GetGuideShowName(response)

  def ProcessFiles(self):
    # Main TVRenamer flow
    ## Get Unique file show names
    ## Get actual show name & corresponding IDs
    ## Get Episode names
    ## Generate new file paths
    ## Rename files
    showNameMatchDict = {}
    uniqueFileShowList = self._GetUniqueFileShowNames(self._fileList)
    #print(uniqueFileShowList)
    for fileShowName in uniqueFileShowList:
      showNameMatchDict[fileShowName] = self._GetGuideShowName(fileShowName)
    raise Exception("STOP HERE")

    for tvFile in self._fileList:
      guideShowName = showNameMatchDict[tvFile.fileShowName]
      episodeName = self._guide.GetEpisodeName(guideShowName, tvFile.season, tvFile.episode)
    #self.RenameFiles(tvFileList)


