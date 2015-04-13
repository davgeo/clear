''' RENAMER '''
# Python default package imports

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

  def GenerateNewFileInfo(self):
    for tvFile in self._fileList:
      print("\n*** -------------------------------- ***")
      episodeName = self._guide.EpisodeLookUp(tvFile.showName, tvFile.seasonNum, tvFile.episodeNum)
      tvFile.UpdateEpisodeName(episodeName)
      print(tvFile.Convert2String())
      #raise Exception("TEST END")

  def RenameFiles(self):
    print("Renaming files...")
