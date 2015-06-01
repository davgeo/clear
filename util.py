''' Utility functions '''

# Python default package imports
import difflib
import glob
import os
import re
import sys

# Python custom package imports
import requests

# Local file imports
import tvfile
import logzila

############################################################################
# CheckPathExists
#
############################################################################
def CheckPathExists(path):
  i = 0
  root, ext = os.path.splitext(path)
  while os.path.exists(path):
    i = i + 1
    logzila.Log.Info("UTIL", "Path {0} already exists".format(path))
    path = "{0}_{1}".format(root, i) + ext
  return path

############################################################################
# StripSpecialCharacters
#
############################################################################
def StripSpecialCharacters(string):
  logzila.Log.Info("UTIL", "Stripping any special characters from {0}".format(string))
  string = re.sub('[&]', 'and', string)
  string = re.sub('[@#$%^&*{};:,/<>?\|`~=+]', '', string)
  string = re.sub('\s\s+', ' ', string)
  logzila.Log.Info("UTIL", "New string is: {0}".format(string))
  return string

#################################################
# CheckEmptyResponse
#################################################
def CheckEmptyResponse(response):
  while response.strip() == '':
    response = logzila.Log.Input("RENAMER", "An empty response was detected - please reenter a valid response: ")
  return response

#################################################
# ValidUserResponse
#################################################
def ValidUserResponse(response, validList):
  if response in validList:
    return response
  else:
    prompt = "Unknown response given - please reenter one of [{0}]: ".format('/'.join(validList))
    response = logzila.Log.Input("DM", prompt)
    self._CheckAcceptableUserResponse(response, validList)

############################################################################
# UserAcceptance
############################################################################
def UserAcceptance(
  matchList,
  recursiveLookup = True,
  promptComment = None,
  promptOnly = False,
  xStrOverride = "to skip this selection"
):
  matchString = ', '.join(matchList)

  if len(matchList) == 1:
    logzila.Log.Info("UTIL", "Match found: {0}".format(matchString))
    prompt = "Enter 'y' to accept this match or e"
  elif len(matchList) > 1:
    logzila.Log.Info("UTIL", "Multiple possible matches found: {0}".format(matchString))
    prompt = "Enter correct match from list or e"
    option = 2
  else:
    if promptOnly is False:
      logzila.Log.Info("UTIL", "No match found")
    prompt = "E"
    if not recursiveLookup:
      return None

  if recursiveLookup:
    prompt = prompt + "nter a different string to look up or e"

  prompt = prompt + "nter 'x' {0} or enter 'exit' to quit this program".format(xStrOverride)

  if promptComment is None:
    prompt = prompt + ": "
  else:
    prompt = prompt + " ({0}): ".format(promptComment)

  while(1):
    response = logzila.Log.Input('UTIL', prompt)

    if response.lower() == 'exit':
      logzila.Log.Info("UTIL", "Program terminated by user 'exit'")
      sys.exit(0)
    if response.lower() == 'x':
      return None
    elif response.lower() == 'y' and len(matchList) == 1:
      return matchList[0]
    elif len(matchList) > 1:
      for match in matchList:
        if response.lower() == match.lower():
          return match
    if recursiveLookup:
      return response

############################################################################
# GetBestMatch
############################################################################
def GetBestMatch(target, matchList):
  bestMatchList = []
  if len(matchList) > 0:
    ratioMatch = []
    for item in matchList:
      ratioMatch.append(GetBestStringMatchValue(target, item))

    maxRatio = max(ratioMatch)
    if maxRatio > 0.8:
      matchIndexList = [i for i, j in enumerate(ratioMatch) if j == maxRatio]

      for index in matchIndexList:
        bestMatchList.append(matchList[index])
  return bestMatchList

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
# Default encoding is UTF8
############################################################################
def WebLookup(url, urlQuery=None, utf8=True):
  # Look up webpage at given url with optional query string
  logzila.Log.Info("UTIL", "Looking up info from URL:{0} with QUERY:{1})".format(url, urlQuery))
  response = requests.get(url, params=urlQuery)
  if utf8 is True:
    response.encoding = 'utf-8'
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
        logzila.Log.Info("UTIL", "Ignoring unsupported file or folder: {0}".format(globPath))
  else:
    logzila.Log.Info("UTIL", "Invalid non-directory path given to parse")

