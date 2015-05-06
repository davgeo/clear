''' DATABASE '''
# Python default package imports
import sqlite3

# Local file imports
import logzila

#################################################
# RenamerDB
#################################################
class RenamerDB:
  #################################################
  # constructor
  #################################################
  def __init__(self, dbPath):
    self._dbPath = dbPath

  #################################################
  # _QueryDatabase
  #################################################
  def _QueryDatabase(self, query, tuples = None, commit = True, error = True):
    logzila.Log.Info("DB", "Database Query: {0} {1}".format(query, tuples))
    with sqlite3.connect(self._dbPath) as db:
      try:
        if tuples is None:
          result = db.execute(query)
        else:
          result = db.execute(query, tuples)
      except sqlite3.OperationalError:
        if error is True:
          raise
        return None
      else:
        if commit is True:
          db.commit()
        return result.fetchall()

  #################################################
  # DropTable
  #################################################
  def DropTable(self, tableName):
    logzila.Log.Info("DB", "Deleting table {0}".format(tableName))
    self._QueryDatabase("DROP TABLE {0}".format(tableName))

  #################################################
  # SetConfigValue
  #################################################
  def SetConfigValue(self, fieldName, value):
    tableExists = self._QueryDatabase("CREATE TABLE Config (Name text, Value text)", error = False)

    if tableExists is None:
      currentConfigValue = self.GetConfigValue(fieldName)
    else:
      currentConfigValue = None

    if currentConfigValue is None:
      logzila.Log.Info("DB", "Adding {0}={1} to database config table".format(fieldName, value))
      self._QueryDatabase("INSERT INTO Config VALUES (?,?)", (fieldName, value))
    else:
      logzila.Log.Info("DB", "Updating {0} in database config table from {1} to {2}".format(fieldName, currentEntry, value))
      self._QueryDatabase("UPDATE Config SET Value=?, WHERE Name=?", (value, fieldName))

  #################################################
  # GetConfigValue
  #################################################
  def GetConfigValue(self, fieldName):
    result = self._QueryDatabase("SELECT Value FROM Config WHERE Name=?", (fieldName, ), error = False)

    if result is None:
      return None
    elif len(result) == 0:
      return None
    elif len(result) == 1:
      logzila.Log.Info("DB", "Found database match in config table {0}={1}".format(fieldName, result[0][0]))
      return result[0][0]
    elif len(result) > 1:
      logzila.Log.Info("DB", "Database corrupted - multiple matches found in config table {0}={1}".format(fieldName, result))
      raise Exception("Corrupted database")

  #################################################
  # _AddToSingleColumnTable
  #################################################
  def _AddToSingleColumnTable(self, tableName, columnHeading, newValue):
    tableExists = self._QueryDatabase("CREATE TABLE {0} ({1} text)".format(tableName, columnHeading), error = False)

    match = None
    if tableExists is None:
      currentTable = self._GetFromSingleColumnTable(tableName)

      if currentTable is not None:
        for currentValue in currentTable:
          if currentValue == newValue:
            match = True

    if match is None:
      logzila.Log.Info("DB", "Adding {0} to {1} table".format(newValue, tableName))
      self._QueryDatabase("INSERT INTO {0} VALUES (?)".format(tableName), (newValue, ))
    else:
      logzila.Log.Info("DB", "{0} already exists in {1} table".format(newValue, tableName))

  #################################################
  # _GetFromSingleColumnTable
  #################################################
  def _GetFromSingleColumnTable(self, tableName):
    table = self._QueryDatabase("SELECT * FROM {0}".format(tableName), error = False)
    if table is None:
      return None
    elif len(table) == 0:
      return None
    elif len(table) > 0:
      tableList = [i[0] for i in table]
      return tableList

  #################################################
  # AddSupportedFormat
  #################################################
  def AddSupportedFormat(self, fileFormat):
    newFileFormat = fileFormat.lower()
    self._AddToSingleColumnTable("SupportedFormat", "FileFormat", newFileFormat)

  #################################################
  # GetSupportedFormats
  #################################################
  def GetSupportedFormats(self):
    formatList = self._GetFromSingleColumnTable("SupportedFormat")
    return formatList

  #################################################
  # AddIgnoredDir
  #################################################
  def AddIgnoredDir(self, ignoredDir):
    self._AddToSingleColumnTable("IgnoredDir", "DirName", ignoredDir)

  #################################################
  # GetIgnoredDirs
  #################################################
  def GetIgnoredDirs(self):
    dirList = self._GetFromSingleColumnTable("IgnoredDir")
    return dirList

  #################################################
  # AddShowToTVLibrary
  #################################################
  def AddShowToTVLibrary(self, showName):
    logzila.Log.Info("DB", "Adding {0} to TV library".format(showName))
    queryStr = ("CREATE TABLE TVLibrary ("
                "ShowID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                "ShowName TEXT UNIQUE NOT NULL, "
                "ShowDir TEXT UNIQUE"
                ")")
    tableExists = self._QueryDatabase(queryStr, error = False)

    if tableExists is None:
      currentShowValues = self.SearchTVLibrary(showName = showName)
    else:
      currentShowValues = None

    if currentShowValues is None:
      self._QueryDatabase("INSERT INTO TVLibrary (ShowName) VALUES (?)", (showName, ))
      showID = self._QueryDatabase("SELECT (ShowID) FROM TVLibrary WHERE ShowName=?", (showName, ))[0][0]
      return showID
    else:
      logzila.Log.Info("DB", "An entry for {0} already exists in the TV library".format(showName))
      raise Exception("Corrupted database")

  #################################################
  # UpdateShowDirInTVLibrary
  #################################################
  def UpdateShowDirInTVLibrary(self, showID, showDir):
    logzila.Log.Info("DB", "Updating TV library for ShowID={0}: ShowDir={1}".format(showID, showDir))
    self._QueryDatabase("UPDATE TVLibrary SET ShowDir=? WHERE ShowID=?", (showDir, showID))

  #################################################
  # SearchTVLibrary
  #################################################
  def SearchTVLibrary(self, showName = None, showID = None, showDir = None):
    unique = True
    if showName is None and showID is None and showDir is None:
      logzila.Log.Info("DB", "Looking up all items in TV library")
      queryString = "SELECT * FROM TVLibrary"
      queryTuple = None
      unique = False
    elif showDir is not None:
      logzila.Log.Info("DB", "Looking up from TV library where ShowDir is {0}".format(showDir))
      queryString = "SELECT * FROM TVLibrary WHERE ShowDir=?"
      queryTuple = (showDir, )
    elif showID is not None:
      logzila.Log.Info("DB", "Looking up from TV library where ShowID is {0}".format(showID))
      queryString = "SELECT * FROM TVLibrary WHERE ShowID=?"
      queryTuple = (showID, )
    elif showName is not None:
      logzila.Log.Info("DB", "Looking up from TV library where ShowName is {0}".format(showName))
      queryString = "SELECT * FROM TVLibrary WHERE ShowName=?"
      queryTuple = (showName, )

    result = self._QueryDatabase(queryString, queryTuple, error = False)

    if result is None:
      return None
    elif len(result) == 0:
      return None
    elif len(result) == 1:
      logzila.Log.Info("DB", "Found match in TVLibrary: {0}".format(result))
      return result
    elif len(result) > 1:
      if unique is True:
        logzila.Log.Info("DB", "Database corrupted - multiple matches found in TV Library: {0}".format(result))
        raise Exception("Corrupted database")
      else:
        logzila.Log.Info("DB", "Found multiple matches in TVLibrary: {0}".format(result))
        return result

  #################################################
  # SearchFileNameTable
  #################################################
  def SearchFileNameTable(self, fileName):
    logzila.Log.Info("DB", "Looking up filename string '{0}' in database".format(fileName))

    queryString = "SELECT ShowID FROM FileName WHERE FileName=?"
    queryTuple = (fileName, )

    result = self._QueryDatabase(queryString, queryTuple, error = False)

    if result is None:
      logzila.Log.Info("DB", "No match found in database for '{0}'".format(fileName))
      return None
    elif len(result) == 0:
      return None
    elif len(result) == 1:
      logzila.Log.Info("DB", "Found file name match: {0}".format(result))
      return result[0][0]
    elif len(result) > 1:
      logzila.Log.Info("DB", "Database corrupted - multiple matches found in database table for: {0}".format(result))
      raise Exception("Corrupted database")

  #################################################
  # AddFileNameTable
  #################################################
  def AddToFileNameTable(self, fileName, showID):
    logzila.Log.Info("DB", "Adding filename string match '{0}'={1} to database".format(fileName, showID))

    queryStr = ("CREATE TABLE FileName ("
                "FileName TEXT UNIQUE NOT NULL, "
                "ShowID INTEGER, "
                "FOREIGN KEY (ShowID) REFERENCES ShowName(ShowID)"
                ")")
    tableExists = self._QueryDatabase(queryStr, error = False)

    if tableExists is None:
      currentValues = self.SearchFileNameTable(fileName)
    else:
      currentValues = None

    if currentValues is None:
      self._QueryDatabase("INSERT INTO FileName (FileName, ShowID) VALUES (?,?)", (fileName, showID))
    else:
      logzila.Log.Info("DB", "An entry for '{0}' already exists in the FileName table".format(fileName))
      raise Exception("Corrupted database")

  #################################################
  # SearchSeasonDirTable
  #################################################
  def SearchSeasonDirTable(self, showID, seasonNum):
    logzila.Log.Info("DB", "Looking up directory for ShowID={0} Season={1} in database".format(showID, seasonNum))

    queryString = "SELECT SeasonDir FROM SeasonDir WHERE ShowID=? AND Season=?"
    queryTuple = (showID, seasonNum)

    result = self._QueryDatabase(queryString, queryTuple, error = False)

    if result is None:
      logzila.Log.Info("DB", "No match found in database")
      return None
    elif len(result) == 0:
      return None
    elif len(result) == 1:
      logzila.Log.Info("DB", "Found database match: {0}".format(result))
      return result[0][0]
    elif len(result) > 1:
      logzila.Log.Info("DB", "Database corrupted - multiple matches found in database table for: {0}".format(result))
      raise Exception("Corrupted database")

  #################################################
  # AddSeasonDirTable
  #################################################
  def AddSeasonDirTable(self, showID, seasonNum, seasonDir):
    logzila.Log.Info("DB", "Adding season directory ({0}) to database for ShowID={1}, Season={2}".format(seasonDir, showID, seasonNum))

    queryStr = ("CREATE TABLE SeasonDir ("
                "SeasonDir TEXT NOT NULL, "
                "Season INTEGER NOT NULL, "
                "ShowID INTEGER, "
                "FOREIGN KEY (ShowID) REFERENCES ShowName(ShowID),"
                "CONSTRAINT SeasonDirPK PRIMARY KEY (ShowID,Season)"
                ")")
    tableExists = self._QueryDatabase(queryStr, error = False)

    if tableExists is None:
      currentValues = self.SearchSeasonDirTable(showID, seasonNum)
    else:
      currentValues = None

    if currentValues is None:
      self._QueryDatabase("INSERT INTO SeasonDir (SeasonDir, Season, ShowID) VALUES (?,?,?)", (seasonDir, seasonNum, showID))
    else:
      logzila.Log.Info("DB", "An entry already exists in the SeasonDir table")
      raise Exception("Corrupted database")
