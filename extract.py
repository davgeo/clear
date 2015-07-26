#!/usr/bin/env python3

''' RAR EXTRACTER '''
# Python default package imports
import sys
import os
import glob
import re

# Third-party python package imports
import rarfile

# Local file imports
import logzila
import util

############################################################################
# GetCompressedFilesInDir
# Get all supported files from given directory folder
############################################################################
def GetCompressedFilesInDir(fileDir, fileList, ignoreDirList, supportedFormatList = ['.rar',]):
  logzila.Log.Info("EXTRACT", "Parsing file directory: {0}".format(fileDir))
  if os.path.isdir(fileDir) is True:
    for globPath in glob.glob(os.path.join(fileDir, '*')):
      if os.path.splitext(globPath)[1] in supportedFormatList:
        fileList.append(globPath)

############################################################################
# main
############################################################################
def Extract(fileList, tvFormatList):
  logzila.Log.Info("EXTRACT", "Extracting files from compressed archives")
  logzila.Log.IncreaseIndent()
  if len(fileList) == 0:
    logzila.Log.Info("EXTRACT", "No files to extract")
    logzila.Log.DecreaseIndent()
    return

  archiveList = []
  multiPartExtractedList = []
  multiPartSkippedList = []
  for filePath in fileList:
    logzila.Log.Info("EXTRACT", "{0}".format(filePath))
    logzila.Log.IncreaseIndent()
    try:
      rf = rarfile.RarFile(filePath)
    except ImportError:
      logzila.Log.Info("EXTRACT", "Unable to extract - Python needs the rarfile package to be installed (see README for more details)")
    except rarfile.NeedFirstVolume:
      multiPartSkippedList.append(filePath)
      logzila.Log.Info("EXTRACT", "File skipped - this is not the first part of the RAR archive")
    except Exception as ex:
      logzila.Log.Info("EXTRACT", "Unable to extract - Exception ({0}): {1}".format(ex.args[0], ex.args[1]))
    else:
      # TODO: Check for password requirement with user input
      dirPath = os.path.dirname(filePath)
      fileExtracted = False

      for f in rf.infolist():
        if util.FileExtensionMatch(f.filename, tvFormatList):
          logzila.Log.Info("EXTRACT", "Extracting file: {0}".format(f.filename))
          try:
            rf.extract(f, dirPath)
          except Exception as ex:
            logzila.Log.Info("EXTRACT", "Extract failed - check that unrar is installed [Exception ({0}): {1}]\n".format(ex.args[0], ex.args[1]))
          else:
            fileExtracted = True

      if fileExtracted is True:
        archiveList.append(filePath)
        try:
          firstPartFileName = re.findall('(.+?)[.]part1[.]rar', filePath)[0]
        except IndexError:
          pass
        else:
          multiPartExtractedList.append(firstPartFileName)
    finally:
      logzila.Log.DecreaseIndent()

  logzila.Log.DecreaseIndent()
  logzila.Log.NewLine()

  logzila.Log.Info("EXTRACT", "Moving extracted archives to processed directory")
  logzila.Log.IncreaseIndent()
  for filePath in multiPartSkippedList:
    baseFileName = re.findall("(.+?)[.]part.+?rar", filePath)[0]
    if baseFileName in multiPartExtractedList:
      archiveList.append(filePath)

  util.ArchiveProcessedFileList(archiveList)
  logzila.Log.DecreaseIndent()

############################################################################
# default process if run as standalone
############################################################################
if __name__ == "__main__":
  if sys.version_info < (3,4):
    sys.stdout.write("[DM] Incompatible Python version detected - Python 3.4 or greater is required.\n")
  else:
    fileList = []
    GetCompressedFilesInDir('test_dir/downloads', fileList, ['DONE', 'PROCESSED'])
    Extract(fileList, (".mkv", ".mp4", ".avi", ".srt"))
