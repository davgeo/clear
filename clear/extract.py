""" RAR extraction methods """

# Python default package imports
import sys
import os
import glob
import re

# Third-party package imports
import rarfile
import goodlogging

# Local file imports
import clear.util as util

# Update rarfile variables
rarfile.PATH_SEP = os.sep

############################################################################
# GetCompressedFilesInDir
# TODO: Add recursive lookup for nested directory tree
############################################################################
def GetCompressedFilesInDir(fileDir, fileList, ignoreDirList, supportedFormatList = ['.rar',]):
  """
  Get all supported files from given directory folder. Appends to given file list.

  Parameters
  ----------
    fileDir : string
      File directory to search.

    fileList : list
      List which any file matches will be added to.

    ignoreDirList : list
      List of directories to ignore in recursive lookup (currently unused).

    supportedFormatList : list [optional : default = ['.rar',]]
      List of supported file formats to search for.
  """
  goodlogging.Log.Info("EXTRACT", "Parsing file directory: {0}".format(fileDir))
  if os.path.isdir(fileDir) is True:
    for globPath in glob.glob(os.path.join(fileDir, '*')):
      if os.path.splitext(globPath)[1] in supportedFormatList:
        fileList.append(globPath)

############################################################################
# MultipartArchiving
############################################################################
def MultipartArchiving(firstPartExtractList, otherPartSkippedList, archiveDir, otherPartFilePath = None):
  """
  Archive all parts of multi-part compressed file.

  If file has been extracted (via part1) then move all subsequent parts directly to archive directory.
  If file has not been extracted then if part >1 add to other part skipped list and only archive
  when the first part is sent for archiving.

  Parameters
  ----------
    firstPartExtractList : list
      File directory to search.

    otherPartSkippedList : list
      List which any file matches will be added to.

    archiveDir : list
      List of directories to ignore in recursive lookup (currently unused).

    otherPartFilePath : list [optional : default = None]
      List of supported file formats to search for.
  """
  if otherPartFilePath is None:
    for filePath in list(otherPartSkippedList):
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
############################################################################
def DoRarExtraction(rarArchive, targetFile, dstDir):
  """
  RAR extraction with exception catching

  Parameters
  ----------
    rarArchive : RarFile object
      RarFile object to extract.

    targetFile : string
      Target file name.

    dstDir : string
      Target directory.

  Returns
  ----------
    boolean
      False if rar extraction failed, otherwise True.
  """
  try:
    rarArchive.extract(targetFile, dstDir)
  except BaseException as ex:
    goodlogging.Log.Info("EXTRACT", "Extract failed - Exception: {0}".format(ex))
    return False
  else:
    return True

############################################################################
# GetRarPassword
############################################################################
def GetRarPassword(skipUserInput):
  """
  Get password for rar archive from user input.

  Parameters
  ----------
    skipUserInput : boolean
      Set to skip user input.

  Returns
  ----------
    string or boolean
      If no password is given then returns False otherwise returns user
      response string.
  """
  goodlogging.Log.Info("EXTRACT", "RAR file needs password to extract")
  if skipUserInput is False:
    prompt = "Enter password, 'x' to skip this file or 'exit' to quit this program: "
    response = goodlogging.Log.Input("EXTRACT", prompt)
    response = util.CheckEmptyResponse(response)
  else:
    response = 'x'

  if response.lower() == 'x':
    goodlogging.Log.Info("EXTRACT", "File extraction skipped without password")
    return False
  elif response.lower() == 'exit':
    goodlogging.Log.Fatal("EXTRACT", "Program terminated by user 'exit'")
  else:
    return response

############################################################################
# CheckPasswordReuse
############################################################################
def CheckPasswordReuse(skipUserInput):
  """
  Check with user for password reuse.

  Parameters
  ----------
    skipUserInput : boolean
      Set to skip user input.

  Returns
  ----------
    int
      Integer from -1 to 2 depending on user response.
  """
  goodlogging.Log.Info("EXTRACT", "RAR files needs password to extract")
  if skipUserInput is False:
    prompt = "Enter 't' to reuse the last password for just this file, " \
             "'a' to reuse for all subsequent files, " \
             "'n' to enter a new password for this file " \
             "or 's' to enter a new password for all files: "
    response = goodlogging.Log.Input("EXTRACT", prompt)
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
############################################################################
def Extract(fileList, fileFormatList, archiveDir, skipUserInput):
  """
  Iterate through given file list and extract all files matching the file
  format list from each RAR file. After sucessful extraction move RAR files to
  archive directory.

  Parameters
  ----------
    fileList : list
      List of files to attempt to extract.

    fileFormatList : list
      List of file formats to extract from each RAR archive.

    archiveDir : string
      Directory to move RAR files once extract is complete.

    skipUserInput : boolean
      Set to skip any potential user input (if a single option is available
      it will be selected otherwise the user input will default to take no action).
  """
  goodlogging.Log.Info("EXTRACT", "Extracting files from compressed archives")
  goodlogging.Log.IncreaseIndent()
  if len(fileList) == 0:
    goodlogging.Log.Info("EXTRACT", "No files to extract")
    goodlogging.Log.DecreaseIndent()
    return None

  firstPartExtractList = []
  otherPartSkippedList = []

  lastPassword = False
  reuseLastPassword = 0
  for filePath in fileList:
    goodlogging.Log.Info("EXTRACT", "{0}".format(filePath))
    goodlogging.Log.IncreaseIndent()
    try:
      rarArchive = rarfile.RarFile(filePath)
    except ImportError:
      goodlogging.Log.Info("EXTRACT", "Unable to extract - Python needs the rarfile package to be installed (see README for more details)")
    except rarfile.NeedFirstVolume:
      goodlogging.Log.Info("EXTRACT", "File skipped - this is not the first part of the RAR archive")
      MultipartArchiving(firstPartExtractList, otherPartSkippedList, archiveDir, filePath)
    except BaseException as ex:
      goodlogging.Log.Info("EXTRACT", "Unable to extract - Exception: {0}".format(ex))
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
          rarPassword = GetRarPassword(skipUserInput)

          if rarPassword:
            rarArchive.setpassword(rarPassword)
            lastPassword = rarPassword
          else:
            rarAuthentication = False

      if rarAuthentication:
        for f in rarArchive.infolist():
          if util.FileExtensionMatch(f.filename, fileFormatList):
            goodlogging.Log.Info("EXTRACT", "Extracting file: {0}".format(f.filename))

            extractPath = os.path.join(dirPath, f.filename)
            targetPath = os.path.join(dirPath, os.path.basename(f.filename))

            if os.path.isfile(targetPath):
              goodlogging.Log.Info("EXTRACT", "Extraction skipped - file already exists at target: {0}".format(targetPath))
              fileExtracted = True
            elif os.path.isfile(extractPath):
              goodlogging.Log.Info("EXTRACT", "Extraction skipped - file already exists at extract directory: {0}".format(extractPath))
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
      goodlogging.Log.DecreaseIndent()
  goodlogging.Log.DecreaseIndent()
