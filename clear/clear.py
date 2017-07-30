""" Command-Line Extract and Rename tool

This is the entry point for this program. """

# Python default package imports
import os
import sys
import argparse
import glob

# Third-party package imports
import goodlogging

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
  """
  Clear manager class.

  The run method of this class implements the full
  clear flow. This includes parsing script arguments,
  generating a file list (including doing file
  extraction) and finally calling the run method
  of the TVRenamer class.

  This class has no public attributes but a number
  of private attributes are used internally.

  Attributes
  ----------
    _db : RenamerDB class
      Reference to database object.

    _sourceDir : string
      Root of source directory.

    _tvDir : string
      Root directory for renamed TV files.

    _archiveDir : string
      Name of directory to move any deletable
      files (e.g. compressed files after extraction)

    _supportedFormatsList : list
      List of supported formats to process for renaming
      or for file extraction from compressed archives.
      Looked up from database.

    _ignoredDirsList : list
      List of directories to ignore in recursive search
      of files from source directory. Looked up from
      database.

    _databasePath : string
      Path to database file.

    _inPlaceRename : boolean
      Default to False. Set by plusarg. Used to force
      renaming to be done in place (i.e. the target directory
      is the source directory). In this case the value
      of _tvDir is ignored.

    _crossSystemCopyEnabled : boolean
      Default to False. Set by plusarg. Enables copying
      of files if source and target directories exist on
      different file systems.

    _dbUpdate : boolean
      Default to False. Set by plusarg. Enables manual
      updating of database before proceeding with the
      normal job flow.

    _dbPrint : boolean
      Default to False. Set by plusarg. If set prints
      all tables in the database before proceeding with
      the normal job flow.

    _enableExtract : boolean
      Default to False. Set by plusarg. Enables extraction
      of files from compressed archives.

    _skipUserInputRename : boolean
      Default to False. Set by plusarg. If set all user
      input during rename phase is skipped.

    _skipUserInputExtract : boolean
      Default to False. Set by plusarg. If set all user
      input during extract phase is skipped.
  """

  #################################################
  # constructor
  #################################################
  def __init__(self):
    """ Constructor. Initialise object values. """
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
    """
    Allow user to set or update config values in the database table.
    This is always called if no valid entry exists in the table already.

    Parameters
    ----------
      configKey : string
        Name of config field.

      strDescriptor : string
        Description of config field.

      isDir : boolean [optional : default = True]
        Set to True if config value is
        expected to be a directory path.

      dbConfigValue : string [optional : default = None]
        The value of an existing entry
        for the given config field.

    Returns
    ----------
      string
        New value for given config field in database.
    """
    newConfigValue = None

    if dbConfigValue is None:
      prompt = "Enter new {0} or 'x' to exit: ".format(strDescriptor)
    else:
      prompt = "Enter 'y' to use existing {0}, enter a new {0} or 'x' to exit: ".format(strDescriptor)

    while newConfigValue is None:
      response = goodlogging.Log.Input("CLEAR", prompt)

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
          goodlogging.Log.Info("CLEAR", "{0} is not recognised as a directory".format(response))

    return newConfigValue

  ############################################################################
  # _GetConfigValue
  ############################################################################
  def _GetConfigValue(self, configKey, strDescriptor, isDir = True):
    """
    Get configuration value from database table. If no value found user
    will be prompted to enter one.

    Parameters
    ----------
      configKey : string
        Name of config field.

      strDescriptor : string
        Description of config field.

      isDir : boolean [optional : default = True]
        Set to True if config value is
        expected to be a directory path.

    Returns
    ----------
      string
        Value for given config field in database.
    """
    goodlogging.Log.Info("CLEAR", "Loading {0} from database:".format(strDescriptor))
    goodlogging.Log.IncreaseIndent()
    configValue = self._db.GetConfigValue(configKey)

    if configValue is None:
      goodlogging.Log.Info("CLEAR", "No {0} exists in database".format(strDescriptor))
      configValue = self._UserUpdateConfigValue(configKey, strDescriptor, isDir)
    else:
      goodlogging.Log.Info("CLEAR", "Got {0} {1} from database".format(strDescriptor, configValue))


    if not isDir or os.path.isdir(configValue):
      goodlogging.Log.Info("CLEAR", "Using {0} {1}".format(strDescriptor, configValue))
      goodlogging.Log.DecreaseIndent()
      return configValue
    else:
      goodlogging.Log.Info("CLEAR", "Exiting... {0} is not recognised as a directory".format(configValue))
      sys.exit(0)

  ############################################################################
  # _UserUpdateSupportedFormats
  ############################################################################
  def _UserUpdateSupportedFormats(self, origFormatList = []):
    """
    Add supported formats to database table. Always called if the
    database table is empty.

    User can build a list of entries to add to the database table
    (one entry at a time). Once finished they select the finish option
    and all entries will be added to the table. They can reset the
    list at any time before finishing.

    Parameters
    ----------
      origFormatList : list [optional : default = []]
        List of original formats from database table.

    Returns
    ----------
      string
        List of updated formats from database table.
    """
    formatList = list(origFormatList)

    inputDone = None
    while inputDone is None:
      prompt = "Enter new format (e.g. .mp4, .avi), " \
                             "'r' to reset format list, " \
                             "'f' to finish or " \
                             "'x' to exit: "
      response = goodlogging.Log.Input("CLEAR", prompt)

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
    """
    Get supported format values from database table. If no values found user
    will be prompted to enter values for this table.

    Returns
    ----------
      string
        List of supported formats from database table.
    """
    goodlogging.Log.Info("CLEAR", "Loading supported formats from database:")
    goodlogging.Log.IncreaseIndent()
    formatList = self._db.GetSupportedFormats()

    if formatList is None:
      goodlogging.Log.Info("CLEAR", "No supported formats exist in database")
      formatList = self._UserUpdateSupportedFormats()
    else:
      goodlogging.Log.Info("CLEAR", "Got supported formats from database: {0}".format(formatList))

    goodlogging.Log.Info("CLEAR", "Using supported formats: {0}".format(formatList))
    goodlogging.Log.DecreaseIndent()
    return formatList

  ############################################################################
  # _UserUpdateIgnoredDirs
  ############################################################################
  def _UserUpdateIgnoredDirs(self, origIgnoredDirs = []):
    """
    Add ignored directories to database table. Always called if the
    database table is empty.

    User can build a list of entries to add to the database table
    (one entry at a time). Once finished they select the finish option
    and all entries will be added to the table. They can reset the
    list at any time before finishing.

    Parameters
    ----------
      origIgnoredDirs : list [optional : default = []]
        List of original ignored directories from database table.

    Returns
    ----------
      string
        List of updated ignored directories from database table.
    """
    ignoredDirs = list(origIgnoredDirs)

    inputDone = None
    while inputDone is None:
      prompt = "Enter new directory to ignore (e.g. DONE), " \
                           "'r' to reset directory list, " \
                           "'f' to finish or " \
                           "'x' to exit: "
      response = goodlogging.Log.Input("CLEAR", prompt)

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
    """
    Get ignored directories values from database table. If no values found user
    will be prompted to enter values for this table.

    Returns
    ----------
      string
        List of ignored directories from database table.
    """
    goodlogging.Log.Info("CLEAR", "Loading ignored directories from database:")
    goodlogging.Log.IncreaseIndent()
    ignoredDirs = self._db.GetIgnoredDirs()

    if ignoredDirs is None:
      goodlogging.Log.Info("CLEAR", "No ignored directories exist in database")
      ignoredDirs = self._UserUpdateIgnoredDirs()
    else:
      goodlogging.Log.Info("CLEAR", "Got ignored directories from database: {0}".format(ignoredDirs))

    if self._archiveDir not in ignoredDirs:
      ignoredDirs.append(self._archiveDir)

    goodlogging.Log.Info("CLEAR", "Using ignored directories: {0}".format(ignoredDirs))
    goodlogging.Log.DecreaseIndent()
    return ignoredDirs

  ############################################################################
  # GetDatabaseConfig
  ############################################################################
  def _GetDatabaseConfig(self):
    """
    Get all configuration from database.

    This includes values from the Config table as well as populating lists
    for supported formats and ignored directories from their respective
    database tables.
    """
    goodlogging.Log.Seperator()
    goodlogging.Log.Info("CLEAR", "Getting configuration variables...")
    goodlogging.Log.IncreaseIndent()

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

    goodlogging.Log.NewLine()
    goodlogging.Log.Info("CLEAR", "Configuation is:")
    goodlogging.Log.IncreaseIndent()
    goodlogging.Log.Info("CLEAR", "Source directory = {0}".format(self._sourceDir))
    goodlogging.Log.Info("CLEAR", "TV directory = {0}".format(self._tvDir))
    goodlogging.Log.Info("CLEAR", "Supported formats = {0}".format(self._supportedFormatsList))
    goodlogging.Log.Info("CLEAR", "Ignored directory list = {0}".format(self._ignoredDirsList))
    goodlogging.Log.ResetIndent()

  ############################################################################
  # GetArgs
  ############################################################################
  def _GetArgs(self):
    """ Parse plusargs. """
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
      goodlogging.Log.Info("CLEAR", "*WARNING* YOU ARE ABOUT TO DELETE DATABASE {0}".format(self._databasePath))
      response = goodlogging.Log.Input("CLEAR", "Are you sure you want to proceed [y/n]? ")
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
      goodlogging.Log.tagsEnabled = 1

    if args.debug:
      goodlogging.Log.verbosityThreshold = goodlogging.Verbosity.MINIMAL

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
        goodlogging.Log.Fatal("CLEAR", 'Source directory argument is not recognised as a directory: {}'.format(args.src))

    if args.dst:
      if os.path.isdir(args.dst):
        self._tvDir = args.dst
      else:
        goodlogging.Log.Fatal("CLEAR", 'Target directory argument is not recognised as a directory: {}'.format(args.dst))

  ############################################################################
  # GetSupportedFilesInDir
  ############################################################################
  def _GetSupportedFilesInDir(self, fileDir, fileList, supportedFormatList, ignoreDirList):
    """
    Recursively get all supported files given a root search directory.

    Supported file extensions are given as a list, as are any directories which
    should be ignored.

    The result will be appended to the given file list argument.

    Parameters
    ----------
      fileDir : string
        Path to root of directory tree to search.

      fileList : string
        List to add any found files to.

      supportedFormatList : list
        List of supported file extensions.

      ignoreDirList : list
        List of directories to ignore.
    """
    goodlogging.Log.Info("CLEAR", "Parsing file directory: {0}".format(fileDir))
    if os.path.isdir(fileDir) is True:
      for globPath in glob.glob(os.path.join(fileDir, '*')):
        if util.FileExtensionMatch(globPath, supportedFormatList):
          newFile = tvfile.TVFile(globPath)
          if newFile.GetShowDetails():
            fileList.append(newFile)
        elif os.path.isdir(globPath):
          if(os.path.basename(globPath) in ignoreDirList):
            goodlogging.Log.Info("CLEAR", "Skipping ignored directory: {0}".format(globPath))
          else:
            self._GetSupportedFilesInDir(globPath, fileList, supportedFormatList, ignoreDirList)
        else:
          goodlogging.Log.Info("CLEAR", "Ignoring unsupported file or folder: {0}".format(globPath))
    else:
      goodlogging.Log.Info("CLEAR", "Invalid non-directory path given to parse")

  ############################################################################
  # Run
  ############################################################################
  def Run(self):
    """
    Main entry point for ClearManager class.

    Does the following steps:

    - Parse script arguments.
    - Optionally print or update database tables.
    - Get all configuration settings from database.
    - Optionally parse directory for file extraction.
    - Recursively parse source directory for files matching
      supported format list.
    - Call renamer.TVRenamer with file list.
    """
    self._GetArgs()

    goodlogging.Log.Info("CLEAR", "Using database: {0}".format(self._databasePath))
    self._db = database.RenamerDB(self._databasePath)

    if self._dbPrint or self._dbUpdate:
      goodlogging.Log.Seperator()
      self._db.PrintAllTables()

      if self._dbUpdate:
        goodlogging.Log.Seperator()
        self._db.ManualUpdateTables()

    self._GetDatabaseConfig()

    if self._enableExtract:
      goodlogging.Log.Seperator()

      extractFileList = []
      goodlogging.Log.Info("CLEAR", "Parsing source directory for compressed files")
      goodlogging.Log.IncreaseIndent()
      extract.GetCompressedFilesInDir(self._sourceDir, extractFileList, self._ignoredDirsList)
      goodlogging.Log.DecreaseIndent()

      goodlogging.Log.Seperator()
      extract.Extract(extractFileList, self._supportedFormatsList, self._archiveDir, self._skipUserInputExtract)

    goodlogging.Log.Seperator()

    tvFileList = []
    goodlogging.Log.Info("CLEAR", "Parsing source directory for compatible files")
    goodlogging.Log.IncreaseIndent()
    self._GetSupportedFilesInDir(self._sourceDir, tvFileList, self._supportedFormatsList, self._ignoredDirsList)
    goodlogging.Log.DecreaseIndent()

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
  """ Main entry point for clear program """
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
