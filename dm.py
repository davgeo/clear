''' DOWNLOAD MANAGER '''
# Python default package imports

# Custom Python package imports

# Local file imports
import renamer
import database
import util

#################################################
# DownloadManager
#################################################
class DownloadManager:
  #################################################
  # constructor
  #################################################
  def __init__(self, dbPath):
    self._db = database.RenamerDB(dbPath)
    self._downloadDir = None
    self._targetDir = None
    self._supportedFormatsList = []
    self._ignoredDirsList = []

  ############################################################################
  # _GetConfigDir
  ############################################################################
  def _GetConfigDir(self, configKey, strDescriptor):
    print("  [DM] Loading {0} from database:".format(strDescriptor))
    configValue = self._db.GetConfigValue(configKey)
    if configValue is None:
      print("    [DM] No {0} exists in database".format(strDescriptor))

      while configValue is None:
        prompt = "    [DM] Enter new {0} or 'x' to exit: ".format(strDescriptor)
        response = input(prompt)

        if response.lower() == 'x':
          sys.exit(0)
        elif os.path.isdir(response):
          configValue = os.path.abspath(response)
          self._db.SetConfigValue(configKey, configValue)
        else:
          print("    [DM] {0} is not recognised as a directory".format(response))
    print("    [DM] Using {0} {1}".format(strDescriptor, configValue))
    return configValue

  ############################################################################
  # _GetSupportedFormats
  ############################################################################
  def _GetSupportedFormats(self):
    print("  [DM] Loading supported formats from database:")
    formatList = self._db.GetSupportedFormats()
    if formatList is None:
      print("    [DM] No format list exists in database")
      inputDone = None
      formatList = []
      while inputDone is None:
        prompt = "    [DM] Enter new format (e.g. .mp4, .avi)," \
                             "'r' to reset format list, " \
                             "'f' to finish or " \
                             "'x' to exit: "
        response = input(prompt)

        if response.lower() == 'x':
          sys.exit(0)
        elif response.lower() == 'f':
          inputDone = 1
        elif response.lower() == 'r':
          formatList = []
        else:
          if response is not None:
            if(response[0] != '.'):
              response = '.' + response
            formatList.append(response)
      formatList = set(formatList)
      for fileFormat in formatList:
        db.AddSupportedFormat(fileFormat)
    print("    [DM] Using supported formats: {0}".format(formatList))
    return formatList

  ############################################################################
  # GetIgnoredDirs
  ############################################################################
  def _GetIgnoredDirs(self):
    print("  [DM] Loading ignored directories from database:")
    ignoredDirs = self._db.GetIgnoredDirs()
    if ignoredDirs is None:
      print("    [DM] No ignored directories exist in database")
      inputDone = None
      ignoredDirs = []
      while inputDone is None:
        prompt = "    [DM] Enter new directory to ignore (e.g. DONE)," \
                             "'r' to reset directory list, " \
                             "'f' to finish or " \
                             "'x' to exit: "
        response = input(prompt)

        if response.lower() == 'x':
          sys.exit(0)
        elif response.lower() == 'f':
          inputDone = 1
        elif response.lower() == 'r':
          ignoredDirs = []
        else:
          if response is not None:
            ignoredDirs.append(response)
      #ignoredDirs = set(ignoredDirs)
      for ignoredDir in ignoredDirs:
        db.AddIgnoredDir(ignoredDir)
    print("    [DM] Using supported formats: {0}".format(ignoredDirs))
    return ignoredDirs

  ############################################################################
  # GetDatabaseConfig
  ############################################################################
  def _GetDatabaseConfig(self):
    print("\n*** -------------------------------- ***")
    print("[DM] Getting configuration variables...")

    # DOWNLOAD DIRECTORY
    self._downloadDir = self._GetConfigDir('DOWNLOAD_DIR', 'download directory')

    # TARGET DIRECTORY
    self._targetDir = self._GetConfigDir('TARGET_DIR', 'target directory')

    #self._db.DropTable('supported_formats')

    # SUPPORTED FILE FORMATS
    self._supportedFormatsList = self._GetSupportedFormats()

    #self._db.DropTable('ignored_dirs')

    # IGNORED DIRECTORIES
    self._ignoredDirsList = self._GetIgnoredDirs()

    print("Download directory = {0}".format(self._downloadDir))
    print("Target directory = {0}".format(self._targetDir))
    print("Supported formats = {0}".format(self._supportedFormatsList))
    print("Ignored directory list = {0}".format(self._ignoredDirsList))

  ############################################################################
  # ProcessDownloadFolder
  # Get all tv files in download directory
  # Copy-rename files using TVRenamer
  # Move old files in DL directory to PROCESSED folder
  ############################################################################
  def ProcessDownloadFolder(self):
    tvFileList = []
    self._GetDatabaseConfig()
    util.GetSupportedFilesInDir(self._downloadDir, tvFileList, self._supportedFormatsList, self._ignoredDirsList)
    tvRenamer = renamer.TVRenamer(self._db, tvFileList, 'EPGUIDES', self._targetDir)
    tvRenamer.Run()


