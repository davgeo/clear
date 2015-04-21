''' DOWNLOAD MANAGER '''
# Python default package imports

# Custom Python package imports

# Local file imports
import renamer
import database
import util
import logzila

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
    logzila.Log.Info("DM", "Loading {0} from database:".format(strDescriptor))
    logzila.Log.IncreaseIndent()
    configValue = self._db.GetConfigValue(configKey)
    if configValue is None:
      logzila.Log.Info("DM", "No {0} exists in database".format(strDescriptor))

      while configValue is None:
        prompt = "Enter new {0} or 'x' to exit: ".format(strDescriptor)
        response = logzila.Log.Input("DM", prompt)

        if response.lower() == 'x':
          sys.exit(0)
        elif os.path.isdir(response):
          configValue = os.path.abspath(response)
          self._db.SetConfigValue(configKey, configValue)
        else:
          logzila.Log.Info("DM", "{0} is not recognised as a directory".format(response))
    logzila.Log.Info("DM", "Using {0} {1}".format(strDescriptor, configValue))
    logzila.Log.DecreaseIndent()
    return configValue

  ############################################################################
  # _GetSupportedFormats
  ############################################################################
  def _GetSupportedFormats(self):
    logzila.Log.Info("DM", "Loading supported formats from database:")
    logzila.Log.IncreaseIndent()
    formatList = self._db.GetSupportedFormats()
    if formatList is None:
      logzila.Log.Info("DM", "No format list exists in database")
      inputDone = None
      formatList = []
      while inputDone is None:
        prompt = "Enter new format (e.g. .mp4, .avi)," \
                             "'r' to reset format list, " \
                             "'f' to finish or " \
                             "'x' to exit: "
        response = logzila.Log.Input("DM", prompt)

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
    logzila.Log.Info("DM", "Using supported formats: {0}".format(formatList))
    logzila.Log.DecreaseIndent()
    return formatList

  ############################################################################
  # GetIgnoredDirs
  ############################################################################
  def _GetIgnoredDirs(self):
    logzila.Log.Info("DM", "Loading ignored directories from database:")
    logzila.Log.IncreaseIndent()
    ignoredDirs = self._db.GetIgnoredDirs()
    if ignoredDirs is None:
      logzila.Log.Info("DM", "No ignored directories exist in database")
      inputDone = None
      ignoredDirs = []
      while inputDone is None:
        prompt = "Enter new directory to ignore (e.g. DONE)," \
                             "'r' to reset directory list, " \
                             "'f' to finish or " \
                             "'x' to exit: "
        response = logzila.Log.Input("DM", prompt)

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
    logzila.Log.Info("DM", "Using supported formats: {0}".format(ignoredDirs))
    logzila.Log.DecreaseIndent()
    return ignoredDirs

  ############################################################################
  # GetDatabaseConfig
  ############################################################################
  def _GetDatabaseConfig(self):
    logzila.Log.Seperator()
    logzila.Log.Info("DM", "Getting configuration variables...")
    logzila.Log.IncreaseIndent()

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

    logzila.Log.Info("DM", "Download directory = {0}".format(self._downloadDir))
    logzila.Log.Info("DM", "Target directory = {0}".format(self._targetDir))
    logzila.Log.Info("DM", "Supported formats = {0}".format(self._supportedFormatsList))
    logzila.Log.Info("DM", "Ignored directory list = {0}".format(self._ignoredDirsList))
    logzila.Log.DecreaseIndent()

  ############################################################################
  # ProcessDownloadFolder
  # Get all tv files in download directory
  # Copy-rename files using TVRenamer
  # Move old files in DL directory to PROCESSED folder
  ############################################################################
  def ProcessDownloadFolder(self):
    tvFileList = []
    self._GetDatabaseConfig()
    logzila.Log.Seperator()
    util.GetSupportedFilesInDir(self._downloadDir, tvFileList, self._supportedFormatsList, self._ignoredDirsList)
    tvRenamer = renamer.TVRenamer(self._db, tvFileList, 'EPGUIDES', self._targetDir)
    tvRenamer.Run()


