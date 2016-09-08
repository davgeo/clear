'''

CLEAR: Command-Line Extract and Rename tool

This provides RAR extraction and renaming of media files.

'''
# Python default package imports
import os
import sys
import argparse
import glob

# Third-party package imports
import logzilla

# Local file imports
import clear.renamer as renamer
import clear.database as database
import clear.tvfile as tvfile
import clear.util as util
import clear.extract as extract

#################################################
# ClearManager
#################################################
class ClearManager:
  #################################################
  # constructor
  #################################################
  def __init__(self):
    self._db = None
    self._sourceDir = None
    self._tvDir = None
    self._archiveDir = None
    self._supportedFormatsList = []
    self._ignoredDirsList = []
    self._databasePath = 'live.db'
    self._inPlaceRename = False
    self._crossSystemCopyEnabled = False
    self._dbUpdate = False
    self._dbPrint = False
    self._enableExtract = False
    self._skipUserInputRename = False
    self._skipUserInputExtract = False

  ############################################################################
  # _UserUpdateConfigValue
  ############################################################################
  def _UserUpdateConfigValue(self, configKey, strDescriptor, isDir = True, dbConfigValue = None):
    newConfigValue = None

    if dbConfigValue is None:
      prompt = "Enter new {0} or 'x' to exit: ".format(strDescriptor)
    else:
      prompt = "Enter 'y' to use existing {0}, enter a new {0} or 'x' to exit: ".format(strDescriptor)

    while newConfigValue is None:
      response = logzilla.Log.Input("CLEAR", prompt)

      if response.lower() == 'x':
        sys.exit(0)
      elif dbConfigValue is not None and response.lower() == 'y':
        newConfigValue = dbConfigValue
      elif not isDir:
        newConfigValue = response
        self._db.SetConfigValue(configKey, newConfigValue)
      else:
        if os.path.isdir(response):
          newConfigValue = os.path.abspath(response)
          self._db.SetConfigValue(configKey, newConfigValue)
        else:
          logzilla.Log.Info("CLEAR", "{0} is not recognised as a directory".format(response))

    return newConfigValue

  ############################################################################
  # _GetConfigValue
  ############################################################################
  def _GetConfigValue(self, configKey, strDescriptor, isDir = True):
    logzilla.Log.Info("CLEAR", "Loading {0} from database:".format(strDescriptor))
    logzilla.Log.IncreaseIndent()
    configValue = self._db.GetConfigValue(configKey)

    if configValue is None:
      logzilla.Log.Info("CLEAR", "No {0} exists in database".format(strDescriptor))
      configValue = self._UserUpdateConfigValue(configKey, strDescriptor, isDir)
    else:
      logzilla.Log.Info("CLEAR", "Got {0} {1} from database".format(strDescriptor, configValue))


    if not isDir or os.path.isdir(configValue):
      logzilla.Log.Info("CLEAR", "Using {0} {1}".format(strDescriptor, configValue))
      logzilla.Log.DecreaseIndent()
      return configValue
    else:
      logzilla.Log.Info("CLEAR", "Exiting... {0} is not recognised as a directory".format(configValue))
      sys.exit(0)

  ############################################################################
  # _UserUpdateSupportedFormats
  ############################################################################
  def _UserUpdateSupportedFormats(self, origFormatList = []):
    formatList = list(origFormatList)

    inputDone = None
    while inputDone is None:
      prompt = "Enter new format (e.g. .mp4, .avi), " \
                             "'r' to reset format list, " \
                             "'f' to finish or " \
                             "'x' to exit: "
      response = logzilla.Log.Input("CLEAR", prompt)

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
    origFormatList = set(origFormatList)

    if formatList != origFormatList:
      self._db.PurgeSupportedFormats()
      for fileFormat in formatList:
        self._db.AddSupportedFormat(fileFormat)

    return formatList

  ############################################################################
  # _GetSupportedFormats
  ############################################################################
  def _GetSupportedFormats(self):
    logzilla.Log.Info("CLEAR", "Loading supported formats from database:")
    logzilla.Log.IncreaseIndent()
    formatList = self._db.GetSupportedFormats()

    if formatList is None:
      logzilla.Log.Info("CLEAR", "No supported formats exist in database")
      formatList = self._UserUpdateSupportedFormats()
    else:
      logzilla.Log.Info("CLEAR", "Got supported formats from database: {0}".format(formatList))

    logzilla.Log.Info("CLEAR", "Using supported formats: {0}".format(formatList))
    logzilla.Log.DecreaseIndent()
    return formatList

  ############################################################################
  # _UserUpdateIgnoredDirs
  ############################################################################
  def _UserUpdateIgnoredDirs(self, origIgnoredDirs = []):
    ignoredDirs = list(origIgnoredDirs)

    inputDone = None
    while inputDone is None:
      prompt = "Enter new directory to ignore (e.g. DONE), " \
                           "'r' to reset directory list, " \
                           "'f' to finish or " \
                           "'x' to exit: "
      response = logzilla.Log.Input("CLEAR", prompt)

      if response.lower() == 'x':
        sys.exit(0)
      elif response.lower() == 'f':
        inputDone = 1
      elif response.lower() == 'r':
        ignoredDirs = []
      else:
        if response is not None:
          ignoredDirs.append(response)

    ignoredDirs = set(ignoredDirs)
    origIgnoredDirs = set(origIgnoredDirs)

    if ignoredDirs != origIgnoredDirs:
      self._db.PurgeIgnoredDirs()
      for ignoredDir in ignoredDirs:
        self._db.AddIgnoredDir(ignoredDir)

    return list(ignoredDirs)

  ############################################################################
  # GetIgnoredDirs
  ############################################################################
  def _GetIgnoredDirs(self):
    logzilla.Log.Info("CLEAR", "Loading ignored directories from database:")
    logzilla.Log.IncreaseIndent()
    ignoredDirs = self._db.GetIgnoredDirs()

    if ignoredDirs is None:
      logzilla.Log.Info("CLEAR", "No ignored directories exist in database")
      ignoredDirs = self._UserUpdateIgnoredDirs()
    else:
      logzilla.Log.Info("CLEAR", "Got ignored directories from database: {0}".format(ignoredDirs))

    if self._archiveDir not in ignoredDirs:
      ignoredDirs.append(self._archiveDir)

    logzilla.Log.Info("CLEAR", "Using ignored directories: {0}".format(ignoredDirs))
    logzilla.Log.DecreaseIndent()
    return ignoredDirs

  ############################################################################
  # GetDatabaseConfig
  ############################################################################
  def _GetDatabaseConfig(self):
    logzilla.Log.Seperator()
    logzilla.Log.Info("CLEAR", "Getting configuration variables...")
    logzilla.Log.IncreaseIndent()

    # SOURCE DIRECTORY
    if self._sourceDir is None:
      self._sourceDir = self._GetConfigValue('SourceDir', 'source directory')

    # TV DIRECTORY
    if self._inPlaceRename is False and self._tvDir is None:
      self._tvDir = self._GetConfigValue('TVDir', 'tv directory')

    # ARCHIVE DIRECTORY
    self._archiveDir = self._GetConfigValue('ArchiveDir', 'archive directory', isDir = False)

    # SUPPORTED FILE FORMATS
    self._supportedFormatsList = self._GetSupportedFormats()

    # IGNORED DIRECTORIES
    self._ignoredDirsList = self._GetIgnoredDirs()

    logzilla.Log.NewLine()
    logzilla.Log.Info("CLEAR", "Configuation is:")
    logzilla.Log.IncreaseIndent()
    logzilla.Log.Info("CLEAR", "Source directory = {0}".format(self._sourceDir))
    logzilla.Log.Info("CLEAR", "TV directory = {0}".format(self._tvDir))
    logzilla.Log.Info("CLEAR", "Supported formats = {0}".format(self._supportedFormatsList))
    logzilla.Log.Info("CLEAR", "Ignored directory list = {0}".format(self._ignoredDirsList))
    logzilla.Log.ResetIndent()

  ############################################################################
  # GetArgs
  ############################################################################
  def _GetArgs(self):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--src', help='override database source directory')
    parser.add_argument('-d', '--dst', help='override database destination directory')

    parser.add_argument('-e', '--extract', help='enable extracting of rar files', action="store_true")

    parser.add_argument('-c', '--copy', help='enable copying between file systems', action="store_true")
    parser.add_argument('-i', '--inplace', help='rename files in place', action="store_true")

    parser.add_argument('-u', '--update_db', help='provides option to update existing database fields', action="store_true")
    parser.add_argument('-p', '--print_db', help='print contents of database', action="store_true")

    parser.add_argument('-n', '--no_input', help='automatically accept or skip all user input', action="store_true")
    parser.add_argument('-nr', '--no_input_rename', help='automatically accept or skip user input for guide lookup and rename', action="store_true")
    parser.add_argument('-ne', '--no_input_extract', help='automatically accept or skip user input for extraction', action="store_true")

    parser.add_argument('--debug', help='enable full logging', action="store_true")
    parser.add_argument('--tags', help='enable tags on log info', action="store_true")

    parser.add_argument('--test', help='run with test database', action="store_true")
    parser.add_argument('--reset', help='resets database', action="store_true")

    args = parser.parse_args()

    if args.test:
      self._databasePath = 'test.db'

    if args.no_input or args.no_input_rename:
      self._skipUserInputRename = True

    if args.no_input or args.no_input_extract:
      self._skipUserInputExtract = True

    if args.reset:
      logzilla.Log.Info("CLEAR", "*WARNING* YOU ARE ABOUT TO DELETE DATABASE {0}".format(self._databasePath))
      response = logzilla.Log.Input("CLEAR", "Are you sure you want to proceed [y/n]? ")
      if response.lower() == 'y':
        if(os.path.isfile(self._databasePath)):
          os.remove(self._databasePath)
      else:
        sys.exit(0)

    if args.inplace:
      self._inPlaceRename = True

    if args.copy:
      self._crossSystemCopyEnabled = True

    if args.tags:
      logzilla.Log.tagsEnabled = 1

    if args.debug:
      logzilla.Log.verbosityThreshold = logzilla.Verbosity.MINIMAL

    if args.update_db:
      self._dbUpdate = True

    if args.print_db:
      self._dbPrint = True

    if args.extract:
      self._enableExtract = True

    if args.src:
      if os.path.isdir(args.src):
        self._sourceDir = args.src
      else:
        logzilla.Log.Fatal("CLEAR", 'Source directory argument is not recognised as a directory: {}'.format(args.src))

    if args.dst:
      if os.path.isdir(args.dst):
        self._tvDir = args.dst
      else:
        logzilla.Log.Fatal("CLEAR", 'Target directory argument is not recognised as a directory: {}'.format(args.dst))

  ############################################################################
  # GetSupportedFilesInDir
  # Get all supported files from given directory folder
  ############################################################################
  def _GetSupportedFilesInDir(self, fileDir, fileList, supportedFormatList, ignoreDirList):
    logzilla.Log.Info("CLEAR", "Parsing file directory: {0}".format(fileDir))
    if os.path.isdir(fileDir) is True:
      for globPath in glob.glob(os.path.join(fileDir, '*')):
        if util.FileExtensionMatch(globPath, supportedFormatList):
          newFile = tvfile.TVFile(globPath)
          if newFile.GetShowDetails():
            fileList.append(newFile)
        elif os.path.isdir(globPath):
          if(os.path.basename(globPath) in ignoreDirList):
            logzilla.Log.Info("CLEAR", "Skipping ignored directory: {0}".format(globPath))
          else:
            self._GetSupportedFilesInDir(globPath, fileList, supportedFormatList, ignoreDirList)
        else:
          logzilla.Log.Info("CLEAR", "Ignoring unsupported file or folder: {0}".format(globPath))
    else:
      logzilla.Log.Info("CLEAR", "Invalid non-directory path given to parse")

  ############################################################################
  # Run
  # Get all tv files in source directory
  # Run renamer process
  ############################################################################
  def Run(self):
    self._GetArgs()

    logzilla.Log.Info("CLEAR", "Using database: {0}".format(self._databasePath))
    self._db = database.RenamerDB(self._databasePath)

    if self._dbPrint or self._dbUpdate:
      logzilla.Log.Seperator()
      self._db.PrintAllTables()

      if self._dbUpdate:
        logzilla.Log.Seperator()
        self._db.ManualUpdateTables()

    self._GetDatabaseConfig()

    if self._enableExtract:
      logzilla.Log.Seperator()

      extractFileList = []
      logzilla.Log.Info("CLEAR", "Parsing source directory for compressed files")
      logzilla.Log.IncreaseIndent()
      extract.GetCompressedFilesInDir(self._sourceDir, extractFileList, self._ignoredDirsList)
      logzilla.Log.DecreaseIndent()

      logzilla.Log.Seperator()
      extract.Extract(extractFileList, self._supportedFormatsList, self._archiveDir, self._skipUserInputExtract)

    logzilla.Log.Seperator()

    tvFileList = []
    logzilla.Log.Info("CLEAR", "Parsing source directory for compatible files")
    logzilla.Log.IncreaseIndent()
    self._GetSupportedFilesInDir(self._sourceDir, tvFileList, self._supportedFormatsList, self._ignoredDirsList)
    logzilla.Log.DecreaseIndent()

    tvRenamer = renamer.TVRenamer(self._db,
                                  tvFileList,
                                  self._archiveDir,
                                  guideName = 'EPGUIDES',
                                  destDir = self._tvDir,
                                  inPlaceRename = self._inPlaceRename,
                                  forceCopy = self._crossSystemCopyEnabled,
                                  skipUserInput = self._skipUserInputRename)
    tvRenamer.Run()

############################################################################
# main
############################################################################
def main():
  prog = ClearManager()
  prog.Run()

############################################################################
# default process if run as standalone
############################################################################
if __name__ == "__main__":
  if sys.version_info < (3,4):
    sys.stdout.write("[CLEAR] Incompatible Python version detected - Python 3.4 or greater is required.\n")
  else:
    main()
