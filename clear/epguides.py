""" Lookup TV guide information from epguides """

# Python default package imports
import os
import glob
import csv
import datetime

# Third-party package imports
import goodlogging

# Local file imports
import clear.util as util

#################################################
# EPGuidesLookup
#################################################
class EPGuidesLookup:
  """
  TV guide lookup class using epguides. Used to
  lookup show and episode names for TV shows.

  Attributes
  ----------
    GUIDE_NAME : string
      Tag used to name this guide.

    ALLSHOW_IDLIST_URL : string
      URL for looking up TV show names.

    EPISODE_LOOKUP_URL : string
      URL for looking up specific show
      information.

    ID_LOOKUP_TAG : string
      Column reference to look up id from
      epguides allshow list.

    EP_LOOKUP_TAG : string
      Parameter used with EPISODE_LOOKUP_URL to
      select specific show to lookup.

    logVerbosity : goodlogging.Verbosity type
      Define the logging verbosity for the class.

    _allShowList : csv
      Contents of allshows lookup.

    _showInfoDict : dict
      Dictionary matching show ID to csv
      contents of lookup for specific show.

    _showTitleList : list
      List of show titles from allshows content.

    _showIDList : list
      List of show ids from allshows content.

    _saveDir : string
      Directory where allshows csv file can be
      saved.
  """
  GUIDE_NAME = 'EPGUIDES'
  ALLSHOW_IDLIST_URL = 'http://epguides.com/common/allshows.txt'
  EPISODE_LOOKUP_URL = 'http://epguides.com/common/exportToCSVmaze.asp'
  ID_LOOKUP_TAG = 'TVmaze'
  EP_LOOKUP_TAG = 'maze'

  logVerbosity = goodlogging.Verbosity.MINIMAL

  #################################################
  # constructor
  #################################################
  def __init__(self):
    """ Constructor. Initialise object values. """
    self._allShowList = None
    self._showInfoDict = {}
    self._showTitleList = None
    self._showIDList = None
    self._saveDir = os.getcwd()

  # *** INTERNAL CLASSES *** #
  ############################################################################
  # _ParseShowList
  ############################################################################
  def _ParseShowList(self, checkOnly=False):
    """
    Read self._allShowList as csv file and make list of titles and IDs.

    Parameters
    ----------
      checkOnly : boolean [optional : default = False]
          If checkOnly is True this will only check to ensure the column
          headers can be extracted correctly.
    """
    showTitleList = []
    showIDList = []

    csvReader = csv.reader(self._allShowList.splitlines())
    for rowCnt, row in enumerate(csvReader):
      if rowCnt == 0:
        # Get header column index
        for colCnt, column in enumerate(row):
          if column == 'title':
            titleIndex = colCnt
          if column == self.ID_LOOKUP_TAG:
            lookupIndex = colCnt
      else:
        try:
          showTitleList.append(row[titleIndex])
          showIDList.append(row[lookupIndex])
        except UnboundLocalError:
          goodlogging.Log.Fatal("EPGUIDE", "Error detected in EPGUIDES allshows csv content")
        else:
          if checkOnly and rowCnt > 1:
            return True
    self._showTitleList = showTitleList
    self._showIDList = showIDList
    return True

  ############################################################################
  # _GetAllShowList
  ############################################################################
  def _GetAllShowList(self):
    """
    Populates self._allShowList with the epguides all show info.

    On the first lookup for a day the information will be loaded from
    the epguides url. This will be saved to local file _epguides_YYYYMMDD.csv
    and any old files will be removed. Subsequent accesses for the same day
    will read this file.
    """
    today = datetime.date.today().strftime("%Y%m%d")
    saveFile = '_epguides_' + today + '.csv'
    saveFilePath = os.path.join(self._saveDir, saveFile)
    if os.path.exists(saveFilePath):
      # Load data previous saved to file
      with open(saveFilePath, 'r') as allShowsFile:
        self._allShowList = allShowsFile.read()
    else:
      # Download new list from EPGUIDES and strip any leading or trailing whitespace
      self._allShowList = util.WebLookup(self.ALLSHOW_IDLIST_URL).strip()

      if self._ParseShowList(checkOnly=True):
        # Save to file to avoid multiple url requests in same day
        with open(saveFilePath, 'w') as allShowsFile:
          goodlogging.Log.Info("EPGUIDE", "Adding new EPGUIDES file: {0}".format(saveFilePath), verbosity=self.logVerbosity)
          allShowsFile.write(self._allShowList)

        # Delete old copies of this file
        globPattern = '_epguides_????????.csv'
        globFilePath = os.path.join(self._saveDir, globPattern)
        for filePath in glob.glob(globFilePath):
          if filePath != saveFilePath:
            goodlogging.Log.Info("EPGUIDE", "Removing old EPGUIDES file: {0}".format(filePath), verbosity=self.logVerbosity)
            os.remove(filePath)

  ############################################################################
  # _GetTitleAndIDList
  ############################################################################
  def _GetTitleAndIDList(self):
    """ Get title and id lists from epguides all show info. """
    # Populate self._allShowList if it does not already exist
    if self._allShowList is None:
      self._GetAllShowList()
    self._ParseShowList()

  ############################################################################
  # _GetTitleList
  ############################################################################
  def _GetTitleList(self):
    """ Generate show title list if it does not already exist. """
    if self._showTitleList is None:
      self._GetTitleAndIDList()

  ############################################################################
  # _GetIDList
  ############################################################################
  def _GetIDList(self):
    """ Generate epguides show id list if it does not already exist. """
    if self._showIDList is None:
      self._GetTitleAndIDList()

  ############################################################################
  # _GetShowID
  ############################################################################
  def _GetShowID(self, showName):
    """
    Get epguides show id for a given show name.

    Attempts to match the given show name against a show title in
    self._showTitleList and, if found, returns the corresponding index
    in self._showIDList.

    Parameters
    ----------
      showName : string
        Show name to get show ID for.

    Returns
    ----------
      int or None
        If a show id is found this will be returned, otherwise None is returned.
    """
    self._GetTitleList()
    self._GetIDList()

    for index, showTitle in enumerate(self._showTitleList):
      if showName == showTitle:
        return self._showIDList[index]
    return None

  ############################################################################
  # _ExtractDataFromShowHtml
  # Uses line iteration to extract <pre>...</pre> data block rather than xml
  # because (1) The HTML text can include illegal xml characters (e.g. &)
  #         (2) Using XML parsing opens up attack opportunity
  ############################################################################
  def _ExtractDataFromShowHtml(self, html):
    """
    Extracts csv show data from epguides html source.

    Parameters
    ----------
      html : string
        Block of html text

    Returns
    ----------
       string
        Show data extracted from html text in csv format.
    """
    htmlLines = html.splitlines()
    for count, line in enumerate(htmlLines):
      if line.strip() == r'<pre>':
        startLine = count+1
      if line.strip() == r'</pre>':
        endLine = count

    try:
      dataList = htmlLines[startLine:endLine]
      dataString = '\n'.join(dataList)
      return dataString.strip()
    except:
      raise Exception("Show content not found - check EPGuides html formatting")

  ############################################################################
  # _GetEpisodeName
  ############################################################################
  def _GetEpisodeName(self, showID, season, episode):
    """
    Get episode name from epguides show info.

    Parameters
    ----------
      showID : string
        Identifier matching show in epguides.

      season : int
        Season number.

      epiosde : int
        Epiosde number.

    Returns
    ----------
      int or None
        If an episode name is found this is returned, otherwise the return
        value is None.
    """
    # Load data for showID from dictionary
    showInfo = csv.reader(self._showInfoDict[showID].splitlines())
    for rowCnt, row in enumerate(showInfo):
      if rowCnt == 0:
        # Get header column index
        for colCnt, column in enumerate(row):
          if column == 'season':
            seasonIndex = colCnt
          if column == 'episode':
            episodeIndex = colCnt
          if column == 'title':
            titleIndex = colCnt
      else:
        # Iterate rows until matching season and episode found
        try:
          int(row[seasonIndex])
          int(row[episodeIndex])
        except ValueError:
          # Skip rows which don't provide integer season or episode numbers
          pass
        else:
          if int(row[seasonIndex]) == int(season) and int(row[episodeIndex]) == int(episode):
            goodlogging.Log.Info("EPGUIDE", "Episode name is {0}".format(row[titleIndex]), verbosity=self.logVerbosity)
            return row[titleIndex]
    return None

  # *** EXTERNAL CLASSES *** #
  ############################################################################
  # ShowNameLookUp
  ############################################################################
  def ShowNameLookUp(self, string):
    """
    Attempts to find the best match for the given string in the list of
    epguides show titles. If this list has not previous been generated it
    will be generated first.

    Parameters
    ----------
      string : string
        String to find show name match against.

    Returns
    ----------
      string
        Show name which best matches input string.
    """
    goodlogging.Log.Info("EPGUIDES", "Looking up show name match for string '{0}' in guide".format(string), verbosity=self.logVerbosity)
    self._GetTitleList()
    showName = util.GetBestMatch(string, self._showTitleList)
    return(showName)

  ############################################################################
  # EpisodeNameLookUp
  ############################################################################
  def EpisodeNameLookUp(self, showName, season, episode):
    """
    Get the episode name correspondng to the given show name, season number
    and episode number.

    Parameters
    ----------
      showName : string
        Name of TV show. This must match an entry in the epguides
        title list (this can be achieved by calling ShowNameLookUp first).

      season : int
        Season number.

      epiosde : int
        Epiosde number.

    Returns
    ----------
      string or None
        If an episode name can be found it is returned, otherwise the return
        value is None.
    """
    goodlogging.Log.Info("EPGUIDE", "Looking up episode name for {0} S{1}E{2}".format(showName, season, episode), verbosity=self.logVerbosity)
    goodlogging.Log.IncreaseIndent()
    showID = self._GetShowID(showName)
    if showID is not None:
      try:
        self._showInfoDict[showID]
      except KeyError:
        goodlogging.Log.Info("EPGUIDE", "Looking up info for new show: {0}(ID:{1})".format(showName, showID), verbosity=self.logVerbosity)
        urlData = util.WebLookup(self.EPISODE_LOOKUP_URL, {self.EP_LOOKUP_TAG: showID})
        self._showInfoDict[showID] = self._ExtractDataFromShowHtml(urlData)
      else:
        goodlogging.Log.Info("EPGUIDE", "Reusing show info previous obtained for: {0}({1})".format(showName, showID), verbosity=self.logVerbosity)
      finally:
        episodeName = self._GetEpisodeName(showID, season, episode)
        goodlogging.Log.DecreaseIndent()
        return episodeName
    goodlogging.Log.DecreaseIndent()
