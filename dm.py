#!/usr/bin/env python3

''' DOWNLOAD MANAGER '''
# Python default package imports
import os
import sys
import argparse

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
  def __init__(self):
    self._db = None
    self._downloadDir = None
    self._tvDir = None
    self._supportedFormatsList = []
    self._ignoredDirsList = []
    self._databasePath = 'test.db'
    self._inPlaceRename = False
    self._crossSystemCopyEnabled = False

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

    if os.path.isdir(configValue):
      logzila.Log.Info("DM", "Using {0} {1}".format(strDescriptor, configValue))
      logzila.Log.DecreaseIndent()
      return configValue
    else:
      logzila.Log.Info("DM", "Exiting... {0} is not recognised as a directory".format(configValue))
      sys.exit(0)

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
        self._db.AddSupportedFormat(fileFormat)
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
      ignoredDirs = set(ignoredDirs)
      for ignoredDir in ignoredDirs:
        self._db.AddIgnoredDir(ignoredDir)
    logzila.Log.Info("DM", "Using ignored directories: {0}".format(ignoredDirs))
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
    self._downloadDir = self._GetConfigDir('DownloadDir', 'download directory')

    # TV DIRECTORY
    if self._inPlaceRename is False:
      self._tvDir = self._GetConfigDir('TVDir', 'tv directory')

    # SUPPORTED FILE FORMATS
    self._supportedFormatsList = self._GetSupportedFormats()

    # IGNORED DIRECTORIES
    self._ignoredDirsList = self._GetIgnoredDirs()

    logzila.Log.NewLine()
    logzila.Log.Info("DM", "Configuation is:")
    logzila.Log.IncreaseIndent()
    logzila.Log.Info("DM", "Download directory = {0}".format(self._downloadDir))
    logzila.Log.Info("DM", "TV directory = {0}".format(self._tvDir))
    logzila.Log.Info("DM", "Supported formats = {0}".format(self._supportedFormatsList))
    logzila.Log.Info("DM", "Ignored directory list = {0}".format(self._ignoredDirsList))
    logzila.Log.ResetIndent()

  ############################################################################
  # GetArgs
  ############################################################################
  def _GetArgs(self):
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', help='run with live database', action="store_true")
    parser.add_argument('--reset', help='resets database', action="store_true")
    parser.add_argument('--copy', help='enable copying between file systems', action="store_true")
    parser.add_argument('--inplace', help='rename files in place', action="store_true")
    parser.add_argument('--debug', help='enable full logging', action="store_true")
    parser.add_argument('-t', '--tags', help='enable tags on log info', action="store_true")
    args = parser.parse_args()

    if args.live:
      self._databasePath = 'live.db'

    if args.reset:
      logzila.Log.Info("DM", "*WARNING* YOU ARE ABOUT TO DELETE DATABASE {0}".format(self._databasePath))
      response = logzila.Log.Input("DM", "Are you sure you want to proceed [y/n]? ")
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
      logzila.Log.tagsEnabled = 1

    if args.debug:
      logzila.Log.verbosityThreshold = logzila.Verbosity.MINIMAL

  ############################################################################
  # Run
  # Get all tv files in download directory
  # Run renamer process
  ############################################################################
  def Run(self):
    self._GetArgs()
    logzila.Log.Info("DM", "Using database: {0}".format(self._databasePath))
    self._db = database.RenamerDB(self._databasePath)

    self._GetDatabaseConfig()

    logzila.Log.Seperator()

    tvFileList = []
    logzila.Log.Info("DM", "Parsing download directory for compatible files")
    logzila.Log.IncreaseIndent()
    util.GetSupportedFilesInDir(self._downloadDir, tvFileList, self._supportedFormatsList, self._ignoredDirsList)
    logzila.Log.DecreaseIndent()

    tvRenamer = renamer.TVRenamer(self._db, tvFileList, guideName = 'EPGUIDES', destDir = self._tvDir, inPlaceRename = self._inPlaceRename, forceCopy = self._crossSystemCopyEnabled)
    tvRenamer.Run()

############################################################################
# main
############################################################################
def main():
  prog = DownloadManager()
  prog.Run()

############################################################################
# default process if run as standalone
############################################################################
if __name__ == "__main__":
  if sys.version_info < (3,4):
    sys.stdout.write("[DM] Incompatible Python version detected - Python 3.4 or greater is required.\n")
  else:
    main()
