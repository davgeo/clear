""" Utility functions """

# Python default package imports
import difflib
import os
import re
import sys
import shutil

# Third-party package imports
import requests
import goodlogging

############################################################################
# RemoveEmptyDirectoryTree
############################################################################
def RemoveEmptyDirectoryTree(path, silent = False, recursion = 0):
  """
  Delete tree of empty directories.

  Parameters
  ----------
    path : string
      Path to root of directory tree.

    silent : boolean [optional: default = False]
      Turn off log output.

    recursion : int [optional: default = 0]
      Indicates level of recursion.
  """
  if not silent and recursion is 0:
    goodlogging.Log.Info("UTIL", "Starting removal of empty directory tree at: {0}".format(path))
  try:
    os.rmdir(path)
  except OSError:
    if not silent:
      goodlogging.Log.Info("UTIL", "Removal of empty directory tree terminated at: {0}".format(path))
    return
  else:
    if not silent:
      goodlogging.Log.Info("UTIL", "Directory deleted: {0}".format(path))
    RemoveEmptyDirectoryTree(os.path.dirname(path), silent, recursion + 1)

############################################################################
# CheckPathExists
############################################################################
def CheckPathExists(path):
  """
  Check if path exists, if it does add number to path (incrementing until
  a unique path is found).

  Parameters
  ----------
    path : string
      Path of directory to try.

  Returns
  ----------
    string
      Path of unique directory.
  """
  i = 0
  root, ext = os.path.splitext(path)
  while os.path.exists(path):
    i = i + 1
    goodlogging.Log.Info("UTIL", "Path {0} already exists".format(path))
    path = "{0}_{1}".format(root, i) + ext
  return path

############################################################################
# StripSpecialCharacters
############################################################################
def StripSpecialCharacters(string, stripAll = False):
  """
  Strips special characters, duplicate spaces and post/pre-ceeding spaces.
  Strip on single spaces, periods, hyphens and underscores is conditional on
  if stripAll is set

  Parameters
  ----------
    string : string
      String to strip special characters from.

    stripAll : boolean [optional: default = False]
      If set will also strip single spaces, periods, hyphens and underscores.

  Returns
  ----------
    string
      Resulting string with special characters removed.
  """
  goodlogging.Log.Info("UTIL", "Stripping any special characters from {0}".format(string), verbosity=goodlogging.Verbosity.MINIMAL)
  string = string.strip()
  string = re.sub('[&]', 'and', string)
  string = re.sub(r'[@#$%^&*{};:,/<>?\\|`~=+±§£]', '', string)
  string = re.sub('\s\s+', ' ', string)

  if stripAll:
    string = re.sub('[_.-]', '', string)
    string = re.sub('\s', '', string)

  goodlogging.Log.Info("UTIL", "New string is: {0}".format(string), verbosity=goodlogging.Verbosity.MINIMAL)
  return string

#################################################
# CheckEmptyResponse
#################################################
def CheckEmptyResponse(response):
  """
  If response is an empty string ask user to enter
  a non-empty response. Do not proceed until a non-empty
  response is given.

  Parameters
  ----------
    response : string
      Response string to check.

  Returns
  ----------
    string
      A non-empty response from user input.
  """
  while response.strip() == '':
    response = goodlogging.Log.Input("RENAMER", "An empty response was detected - please reenter a valid response: ")
  return response

#################################################
# ValidUserResponse
#################################################
def ValidUserResponse(response, validList):
  """
  Check if user response is in a list of valid entires.
  If an invalid response is given re-prompt user to enter
  one of the valid options. Do not proceed until a valid entry
  is given.

  Parameters
  ----------
    response : string
      Response string to check.

    validList : list
      A list of valid responses.

  Returns
  ----------
    string
      A valid response string.
  """
  if response in validList:
    return response
  else:
    prompt = "Unknown response given - please reenter one of [{0}]: ".format('/'.join(validList))
    response = goodlogging.Log.Input("DM", prompt)
    return ValidUserResponse(response, validList)

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
  """
  Prompt user to select a entry from a given match list or to enter a new
  string to look up. If the match list is empty user must enter a new string
  or exit.

  Parameters
  ----------
    matchList : list
      A list of entries which the user can select a valid match from.

    recursiveLookup : boolean [optional: default = True]
      Allow user to enter a new string to look up.

    promptComment : string [optional: default = None]
      Add an additional comment on the end of the prompt message.

    promptOnly : boolean [optional: default = False]
      Set to true if match list is expected to be empty. In which case
      the presence of an empty match list will not be mentioned and user
      will be expected to enter a new response to look up.

    xStrOverride : string [optional: default = "to skip this selection"]
      Override the string for 'x' response. This can be used if
      the behaviour of the 'x' response is changed.

  Returns
  ----------
    string or None
      Either a entry from matchList, another valid response or a new
      string to look up. If match list is empty and recursive lookup is
      disabled or if the user response is 'x' this will return None.
  """
  matchString = ', '.join(matchList)

  if len(matchList) == 1:
    goodlogging.Log.Info("UTIL", "Match found: {0}".format(matchString))
    prompt = "Enter 'y' to accept this match or e"
  elif len(matchList) > 1:
    goodlogging.Log.Info("UTIL", "Multiple possible matches found: {0}".format(matchString))
    prompt = "Enter correct match from list or e"
  else:
    if promptOnly is False:
      goodlogging.Log.Info("UTIL", "No match found")
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
    response = goodlogging.Log.Input('UTIL', prompt)

    if response.lower() == 'exit':
      goodlogging.Log.Fatal("UTIL", "Program terminated by user 'exit'")
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
  """
  Finds the elements of matchList which best match the target string.

  Note that this searches substrings so "abc" will have a 100% match in
  both "this is the abc", "abcde" and "abc".

  The return from this function is a list of potention matches which shared
  the same highest match score. If any exact match is found (1.0 score and
  equal size string) this will be given alone.

  Parameters
  ----------
    target : string
      Target string to match.

    matchList : list
      List of strings to match target against.

  Returns
  ----------
    list
      A list of potention matches which share the same highest match score.
      If any exact match is found (1.0 score and equal size string) this
      will be given alone.
  """
  bestMatchList = []

  if len(matchList) > 0:
    ratioMatch = []
    for item in matchList:
      ratioMatch.append(GetBestStringMatchValue(target, item))

    maxRatio = max(ratioMatch)
    if maxRatio > 0.8:
      matchIndexList = [i for i, j in enumerate(ratioMatch) if j == maxRatio]

      for index in matchIndexList:
        if maxRatio == 1 and len(matchList[index]) == len(target):
          return [matchList[index], ]
        else:
          bestMatchList.append(matchList[index])

  return bestMatchList

############################################################################
# GetBestStringMatchValue
############################################################################
def GetBestStringMatchValue(string1, string2):
  """
  Return the value of the highest matching substrings between two strings.

  Parameters
  ----------
    string1 : string
      First string.

    string2 : string
      Second string.

  Returns
  ----------
    int
      Integer value representing the best match found
      between string1 and string2.
  """
  # Ignore case
  string1 = string1.lower()
  string2 = string2.lower()

  # Ignore non-alphanumeric characters
  string1 = ''.join(i for i in string1 if i.isalnum())
  string2 = ''.join(i for i in string2 if i.isalnum())

  # Finding best match value between string1 and string2
  if len(string1) == 0 or len(string2) == 0:
    bestRatio = 0
  elif len(string1) == len(string2):
    match = difflib.SequenceMatcher(None, string1, string2)
    bestRatio = match.ratio()
  else:
    if len(string1) > len(string2):
      shortString = string2
      longString = string1
    else:
      shortString = string1
      longString = string2

    match = difflib.SequenceMatcher(None, shortString, longString)
    bestRatio = match.ratio()

    for block in match.get_matching_blocks():
      subString = longString[block[1]:block[1]+block[2]]
      subMatch = difflib.SequenceMatcher(None, shortString, subString)
      if(subMatch.ratio() > bestRatio):
        bestRatio = subMatch.ratio()

  return(bestRatio)

############################################################################
# WebLookup
############################################################################
def WebLookup(url, urlQuery=None, utf8=True):
  """
  Look up webpage at given url with optional query string

  Parameters
  ----------
    url : string
      Web url.

    urlQuery : dictionary [optional: default = None]
      Parameter to be passed to GET method of requests module

    utf8 : boolean [optional: default = True]
      Set response encoding

  Returns
  ----------
    string
      GET response text
  """

  goodlogging.Log.Info("UTIL", "Looking up info from URL:{0} with QUERY:{1})".format(url, urlQuery), verbosity=goodlogging.Verbosity.MINIMAL)
  response = requests.get(url, params=urlQuery)
  goodlogging.Log.Info("UTIL", "Full url: {0}".format(response.url), verbosity=goodlogging.Verbosity.MINIMAL)
  if utf8 is True:
    response.encoding = 'utf-8'
  if(response.status_code == requests.codes.ok):
    return(response.text)
  else:
    response.raise_for_status()

############################################################################
# ArchiveProcessedFile
# Move file to archive directory (by default this is 'PROCESSED')
############################################################################
def ArchiveProcessedFile(filePath, archiveDir):
  """
  Move file from given file path to archive directory. Note the archive
  directory is relative to the file path directory.

  Parameters
  ----------
    filePath : string
      File path

    archiveDir : string
      Name of archive directory
  """
  targetDir = os.path.join(os.path.dirname(filePath), archiveDir)
  goodlogging.Log.Info("UTIL", "Moving file to archive directory:")
  goodlogging.Log.IncreaseIndent()
  goodlogging.Log.Info("UTIL", "FROM: {0}".format(filePath))
  goodlogging.Log.Info("UTIL", "TO:   {0}".format(os.path.join(targetDir, os.path.basename(filePath))))
  goodlogging.Log.DecreaseIndent()
  os.makedirs(targetDir, exist_ok=True)
  try:
    shutil.move(filePath, targetDir)
  except shutil.Error as ex4:
    err = ex4.args[0]
    goodlogging.Log.Info("UTIL", "Move to archive directory failed - Shutil Error: {0}".format(err))

############################################################################
# FileExtensionMatch
############################################################################
def FileExtensionMatch(filePath, supportedFileTypeList):
  """
  Check whether the file extension matches any of the supported file types.

  Parameters
  ----------
    filePath : string
      File path

    supportedFileTypeList : list
      List of supported file extensions
  """
  return (os.path.splitext(filePath)[1] in supportedFileTypeList)

