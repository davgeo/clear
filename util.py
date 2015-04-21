''' Utility functions '''

# Python default package imports
import difflib
import requests
import glob
import os

# Local file imports
import tvfile
import logzila

############################################################################
# GetBestStringMatchValue
############################################################################
def GetBestStringMatchValue(string1, string2):
  # Ignore case
  string1 = string1.lower()
  string2 = string2.lower()

  # Ignore non-alphanumeric characters
  string1 = ''.join(i for i in string1 if i.isalnum())
  string2 = ''.join(i for i in string2 if i.isalnum())

  #print("Finding best match value between {0} and {1}".format(string1, string2))
  if len(string1) == 0 or len(string2) == 0:
    bestRatio = 0
  elif len(string1) == len(string2):
    match = difflib.SequenceMatcher(None, string1, string2)
    bestRatio = match.ratio()
    #print("Match ratio is {0}".format(bestRatio))
  else:
    if len(string1) > len(string2):
      shortString = string2
      longString = string1
    else:
      shortString = string1
      longString = string2

    match = difflib.SequenceMatcher(None, shortString, longString)
    bestRatio = match.ratio()
    #print("Baseline match ratio is {0}".format(bestRatio))
    for block in match.get_matching_blocks():
      #print(block)
      subString = longString[block[1]:block[1]+block[2]]
      subMatch = difflib.SequenceMatcher(None, shortString, subString)
      #print("Substring ({0}) matches {1} with ratio {2}".format(subString, shortString, subMatch.ratio()))
      if(subMatch.ratio() > bestRatio):
        bestRatio = subMatch.ratio()
        #print("Substring ({0}) matches {1} with ratio {2}".format(subString, shortString, subMatch.ratio()))

  return(bestRatio)

############################################################################
# WebLookup
############################################################################
def WebLookup(url, urlQuery=None):
  # Look up webpage at given url with optional query string
  logzila.Log.Info("UTIL", "Looking up info from URL:{0} with QUERY:{1})".format(url, urlQuery))
  response = requests.get(url, params=urlQuery)
  if(response.status_code == requests.codes.ok):
    return(response.text)
  else:
    response.raise_for_status()

############################################################################
# GetSupportedFilesInDir
# Get all supported files from given directory folder
############################################################################
def GetSupportedFilesInDir(fileDir, fileList, supportedFormatList, ignoreDirList):
  logzila.Log.Info("UTIL", "Parsing file directory: {0}".format(fileDir))
  if os.path.isdir(fileDir) is True:
    for globPath in glob.glob(os.path.join(fileDir, '*')):
      if os.path.splitext(globPath)[1] in supportedFormatList:
        newFile = tvfile.TVFile(globPath)
        if newFile.GetShowDetails():
          fileList.append(newFile)
      elif os.path.isdir(globPath):
        if(os.path.basename(globPath) in ignoreDirList):
          logzila.Log.Info("UTIL", "Skipping ignored directory: {0}".format(globPath))
        else:
          GetSupportedFilesInDir(globPath, fileList, supportedFormatList, ignoreDirList)
      else:
        logzila.Log.Info("UTIL", "Ignoring unsupported file or folder: {0}".format(item))
  else:
    logzila.Log.Info("UTIL", "Invalid non-directory path given to parse")

