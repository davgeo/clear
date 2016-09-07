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
import clear.logzila as logzila
import clear.util as util

# Update rarfile variables
rarfile.PATH_SEP = os.sep

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
        # TODO: Recursive lookup for nested directory tree

############################################################################
# MultipartArchiving
# Archive all parts of multi-part archive only when extracted via part1
############################################################################
def MultipartArchiving(firstPartExtractList, otherPartSkippedList, archiveDir, otherPartFilePath = None):
  if otherPartFilePath is None:
    for filePath in otherPartSkippedList:
      MultipartArchiving(firstPartExtractList, otherPartSkippedList, archiveDir, filePath)
  else:
    baseFileName = re.findall("(.+?)[.]part.+?rar", otherPartFilePath)[0]

    if baseFileName in firstPartExtractList:
      util.ArchiveProcessedFile(otherPartFilePath, archiveDir)
      if otherPartFilePath in otherPartSkippedList:
        otherPartSkippedList.remove(otherPartFilePath)
    elif otherPartFilePath not in otherPartSkippedList:
      otherPartSkippedList.append(otherPartFilePath)

############################################################################
# DoRarExtraction
# RAR extraction with exception catching
############################################################################
def DoRarExtraction(rarArchive, targetFile, dstDir):
  try:
    rarArchive.extract(targetFile, dstDir)
  except BaseException as ex:
    logzila.Log.Info("EXTRACT", "Extract failed - Exception: {0}".format(ex))
    return False
  else:
    return True

############################################################################
# GetRarPassword
# Add extraction password to rar archive
############################################################################
def GetRarPassword(rarArchive, skipUserInput):
  logzila.Log.Info("EXTRACT", "RAR file needs password to extract")
  if skipUserInput is False:
    prompt = "Enter password, 'x' to skip this file or 'exit' to quit this program: "
    response = logzila.Log.Input("EXTRACT", prompt)
    response = util.CheckEmptyResponse(response)
  else:
    response = 'x'

  if response.lower() == 'x':
    logzila.Log.Info("EXTRACT", "File extraction skipped without password")
    return False
  elif response.lower() == 'exit':
    logzila.Log.Fatal("EXTRACT", "Program terminated by user 'exit'")
  else:
    return response

############################################################################
# CheckPasswordReuse
# Check with user for password reuse
############################################################################
def CheckPasswordReuse(skipUserInput):
  logzila.Log.Info("EXTRACT", "RAR files needs password to extract")
  if skipUserInput is False:
    prompt = "Enter 't' to reuse the last password for just this file, " \
             "'a' to reuse for all subsequent files, " \
             "'n' to enter a new password for this file " \
             "or 's' to enter a new password for all files: "
    response = logzila.Log.Input("EXTRACT", prompt)
    response = util.ValidUserResponse(response, ('t','a','n','s'))
  else:
    response = 'a'

  if response.lower() == 's':
    return -1
  if response.lower() == 'n':
    return 0
  elif response.lower() == 't':
    return 1
  elif response.lower() == 'a':
    return 2

############################################################################
# Extract
# Iterate through fileList and extract all files matching fileFormatList
# from each rar file. After sucessful extraction move rar files to archive
# directory.
############################################################################
def Extract(fileList, fileFormatList, archiveDir, skipUserInput):
  logzila.Log.Info("EXTRACT", "Extracting files from compressed archives")
  logzila.Log.IncreaseIndent()
  if len(fileList) == 0:
    logzila.Log.Info("EXTRACT", "No files to extract")
    logzila.Log.DecreaseIndent()
    return

  firstPartExtractList = []
  otherPartSkippedList = []

  lastPassword = False
  reuseLastPassword = 0

  for filePath in fileList:
    logzila.Log.Info("EXTRACT", "{0}".format(filePath))
    logzila.Log.IncreaseIndent()
    try:
      rarArchive = rarfile.RarFile(filePath)
    except ImportError:
      logzila.Log.Info("EXTRACT", "Unable to extract - Python needs the rarfile package to be installed (see README for more details)")
    except rarfile.NeedFirstVolume:
      logzila.Log.Info("EXTRACT", "File skipped - this is not the first part of the RAR archive")
      MultipartArchiving(firstPartExtractList, otherPartSkippedList, archiveDir, filePath)
    except BaseException as ex:
      logzila.Log.Info("EXTRACT", "Unable to extract - Exception: {0}".format(ex))
    else:
      dirPath = os.path.dirname(filePath)
      fileExtracted = False
      rarAuthentication = True

      if rarArchive.needs_password():
        if lastPassword and reuseLastPassword in (0, 1):
          reuseLastPassword = CheckPasswordReuse(skipUserInput)

        if lastPassword and reuseLastPassword in (1, 2):
          rarArchive.setpassword(lastPassword)
        else:
          rarPassword = GetRarPassword(rarArchive, skipUserInput)

          if rarPassword:
            rarArchive.setpassword(rarPassword)
            lastPassword = rarPassword
          else:
            rarAuthentication = False

      if rarAuthentication:
        for f in rarArchive.infolist():
          if util.FileExtensionMatch(f.filename, fileFormatList):
            logzila.Log.Info("EXTRACT", "Extracting file: {0}".format(f.filename))

            extractPath = os.path.join(dirPath, f.filename)
            targetPath = os.path.join(dirPath, os.path.basename(f.filename))

            if os.path.isfile(targetPath):
              logzila.Log.Info("EXTRACT", "Extraction skipped - file already exists at target: {0}".format(targetPath))
              fileExtracted = True
            elif os.path.isfile(extractPath):
              logzila.Log.Info("EXTRACT", "Extraction skipped - file already exists at extract directory: {0}".format(extractPath))
              fileExtracted = True
            else:
              fileExtracted = DoRarExtraction(rarArchive, f, dirPath)

            if os.path.isfile(extractPath) and not os.path.isfile(targetPath):
              os.rename(extractPath, targetPath)
              util.RemoveEmptyDirectoryTree(os.path.dirname(extractPath))

      if fileExtracted is True:
        util.ArchiveProcessedFile(filePath, archiveDir)

        try:
          firstPartFileName = re.findall('(.+?)[.]part1[.]rar', filePath)[0]
        except IndexError:
          pass
        else:
          firstPartExtractList.append(firstPartFileName)
          MultipartArchiving(firstPartExtractList, otherPartSkippedList, archiveDir)

    finally:
      logzila.Log.DecreaseIndent()
  logzila.Log.DecreaseIndent()
