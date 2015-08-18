''' DATABASE '''
# Python default package imports
import sqlite3
import os
import re

# Local file imports
import logzila

#################################################
# RenamerDB
#################################################
class RenamerDB:
  logVerbosity = logzila.Verbosity.MINIMAL

  #################################################
  # constructor
  #################################################
  def __init__(self, dbPath):
    self._dbPath = dbPath

    self._tableDict = {"Config": ('Name', 'Value'),
                       "IgnoredDir": ('DirName',),
                       "SupportedFormat": ('FileFormat',),
                       "TVLibrary": ('ShowID', 'ShowName', 'ShowDir'),
                       "FileName": ('ShowID', 'ShowDir'),
                       "SeasonDir": ('ShowID', 'Season', 'SeasonDir')}

    if not os.path.exists(self._dbPath):
      self._CreateDatabase()
    elif not os.path.isfile(self._dbPath):
      logzila.Log.Fatal("DB", "Database path exists but it is not a file: {0}".format(self._dbPath))

  #################################################
  # _CreateDatabase
  #################################################
  def _CreateDatabase(self):
    logzila.Log.Info("DB", "Initialising new database", verbosity=self.logVerbosity)

    with sqlite3.connect(self._dbPath) as db:
      # Configuration tables
      db.execute("CREATE TABLE Config ("
                  "Name TEXT UNIQUE NOT NULL, "
                  "Value TEXT)")

      db.execute("CREATE TABLE IgnoredDir ("
                  "DirName TEXT UNIQUE NOT NULL")

      db.execute("CREATE TABLE SupportedFormat ("
                  "FileFormat TEXT UNIQUE NOT NULL)")

      # Look-up tables
      db.execute("CREATE TABLE TVLibrary ("
                  "ShowID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                  "ShowName TEXT UNIQUE NOT NULL, "
                  "ShowDir TEXT UNIQUE)")

      db.execute("CREATE TABLE FileName ("
                  "FileName TEXT UNIQUE NOT NULL, "
                  "ShowID INTEGER, "
                  "FOREIGN KEY (ShowID) REFERENCES ShowName(ShowID))")

      db.execute("CREATE TABLE SeasonDir ("
                  "ShowID INTEGER, "
                  "Season INTEGER NOT NULL, "
                  "SeasonDir TEXT NOT NULL, "
                  "FOREIGN KEY (ShowID) REFERENCES ShowName(ShowID),"
                  "CONSTRAINT SeasonDirPK PRIMARY KEY (ShowID,Season))")

      db.commit()

    logzila.Log.Info("DB", "Database initialisation complete", verbosity=self.logVerbosity)

  #################################################
  # _QueryDatabase
  #################################################
  def _QueryDatabase(self, query, tuples = None, commit = True, error = True):
    logzila.Log.Info("DB", "Database Query: {0} {1}".format(query, tuples), verbosity=self.logVerbosity)
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
  # _PurgeTable
  # Deletes all rows without dropping table
  #################################################
  def _PurgeTable(self, tableName):
    logzila.Log.Info("DB", "Deleting all entries from table {0}".format(tableName), verbosity=self.logVerbosity)
    self._QueryDatabase("DELETE FROM {0}".format(tableName))

  #################################################
  # GetConfigValue
  #################################################
  def GetConfigValue(self, fieldName):
    result = self._QueryDatabase("SELECT Value FROM Config WHERE Name=?", (fieldName, ))

    if result is None:
      return None
    elif len(result) == 0:
      return None
    elif len(result) == 1:
      logzila.Log.Info("DB", "Found database match in config table {0}={1}".format(fieldName, result[0][0]), verbosity=self.logVerbosity)
      return result[0][0]
    elif len(result) > 1:
      logzila.Log.Fatal("DB", "Database corrupted - multiple matches found in config table {0}={1}".format(fieldName, result))

  #################################################
  # SetConfigValue
  #################################################
  def SetConfigValue(self, fieldName, value):
    currentConfigValue = self.GetConfigValue(fieldName)

    if currentConfigValue is None:
      logzila.Log.Info("DB", "Adding {0}={1} to database config table".format(fieldName, value), verbosity=self.logVerbosity)
      self._QueryDatabase("INSERT INTO Config VALUES (?,?)", (fieldName, value))
    else:
      logzila.Log.Info("DB", "Updating {0} in database config table from {1} to {2}".format(fieldName, currentConfigValue, value), verbosity=self.logVerbosity)
      self._QueryDatabase("UPDATE Config SET Value=? WHERE Name=?", (value, fieldName))

  #################################################
  # _AddToSingleColumnTable
  #################################################
  def _AddToSingleColumnTable(self, tableName, columnHeading, newValue):
    match = None
    currentTable = self._GetFromSingleColumnTable(tableName)

    if currentTable is not None:
      for currentValue in currentTable:
        if currentValue == newValue:
          match = True

    if match is None:
      logzila.Log.Info("DB", "Adding {0} to {1} table".format(newValue, tableName), verbosity=self.logVerbosity)
      self._QueryDatabase("INSERT INTO {0} VALUES (?)".format(tableName), (newValue, ))
    else:
      logzila.Log.Info("DB", "{0} already exists in {1} table".format(newValue, tableName), verbosity=self.logVerbosity)

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
  # PurgeSupportedFormats
  #################################################
  def PurgeSupportedFormats(self):
    self._PurgeTable("SupportedFormat")

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
  # PurgeIgnoredDirs
  #################################################
  def PurgeIgnoredDirs(self):
    self._PurgeTable("IgnoredDir")

  #################################################
  # AddShowToTVLibrary
  #################################################
  def AddShowToTVLibrary(self, showName):
    logzila.Log.Info("DB", "Adding {0} to TV library".format(showName), verbosity=self.logVerbosity)

    currentShowValues = self.SearchTVLibrary(showName = showName)

    if currentShowValues is None:
      self._QueryDatabase("INSERT INTO TVLibrary (ShowName) VALUES (?)", (showName, ))
      showID = self._QueryDatabase("SELECT (ShowID) FROM TVLibrary WHERE ShowName=?", (showName, ))[0][0]
      return showID
    else:
      logzila.Log.Fatal("DB", "An entry for {0} already exists in the TV library".format(showName))

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
      logzila.Log.Info("DB", "Looking up all items in TV library", verbosity=self.logVerbosity)
      queryString = "SELECT * FROM TVLibrary"
      queryTuple = None
      unique = False
    elif showDir is not None:
      logzila.Log.Info("DB", "Looking up from TV library where ShowDir is {0}".format(showDir), verbosity=self.logVerbosity)
      queryString = "SELECT * FROM TVLibrary WHERE ShowDir=?"
      queryTuple = (showDir, )
    elif showID is not None:
      logzila.Log.Info("DB", "Looking up from TV library where ShowID is {0}".format(showID), verbosity=self.logVerbosity)
      queryString = "SELECT * FROM TVLibrary WHERE ShowID=?"
      queryTuple = (showID, )
    elif showName is not None:
      logzila.Log.Info("DB", "Looking up from TV library where ShowName is {0}".format(showName), verbosity=self.logVerbosity)
      queryString = "SELECT * FROM TVLibrary WHERE ShowName=?"
      queryTuple = (showName, )

    result = self._QueryDatabase(queryString, queryTuple, error = False)

    if result is None:
      return None
    elif len(result) == 0:
      return None
    elif len(result) == 1:
      logzila.Log.Info("DB", "Found match in TVLibrary: {0}".format(result), verbosity=self.logVerbosity)
      return result
    elif len(result) > 1:
      if unique is True:
        logzila.Log.Fatal("DB", "Database corrupted - multiple matches found in TV Library: {0}".format(result))
      else:
        logzila.Log.Info("DB", "Found multiple matches in TVLibrary: {0}".format(result), verbosity=self.logVerbosity)
        return result

  #################################################
  # SearchFileNameTable
  #################################################
  def SearchFileNameTable(self, fileName):
    logzila.Log.Info("DB", "Looking up filename string '{0}' in database".format(fileName), verbosity=self.logVerbosity)

    queryString = "SELECT ShowID FROM FileName WHERE FileName=?"
    queryTuple = (fileName, )

    result = self._QueryDatabase(queryString, queryTuple, error = False)

    if result is None:
      logzila.Log.Info("DB", "No match found in database for '{0}'".format(fileName), verbosity=self.logVerbosity)
      return None
    elif len(result) == 0:
      return None
    elif len(result) == 1:
      logzila.Log.Info("DB", "Found file name match: {0}".format(result), verbosity=self.logVerbosity)
      return result[0][0]
    elif len(result) > 1:
      logzila.Log.Fatal("DB", "Database corrupted - multiple matches found in database table for: {0}".format(result))

  #################################################
  # AddFileNameTable
  #################################################
  def AddToFileNameTable(self, fileName, showID):
    logzila.Log.Info("DB", "Adding filename string match '{0}'={1} to database".format(fileName, showID), verbosity=self.logVerbosity)

    currentValues = self.SearchFileNameTable(fileName)

    if currentValues is None:
      self._QueryDatabase("INSERT INTO FileName (FileName, ShowID) VALUES (?,?)", (fileName, showID))
    else:
      logzila.Log.Fatal("DB", "An entry for '{0}' already exists in the FileName table".format(fileName))

  #################################################
  # SearchSeasonDirTable
  #################################################
  def SearchSeasonDirTable(self, showID, seasonNum):
    logzila.Log.Info("DB", "Looking up directory for ShowID={0} Season={1} in database".format(showID, seasonNum), verbosity=self.logVerbosity)

    queryString = "SELECT SeasonDir FROM SeasonDir WHERE ShowID=? AND Season=?"
    queryTuple = (showID, seasonNum)

    result = self._QueryDatabase(queryString, queryTuple, error = False)

    if result is None:
      logzila.Log.Info("DB", "No match found in database", verbosity=self.logVerbosity)
      return None
    elif len(result) == 0:
      return None
    elif len(result) == 1:
      logzila.Log.Info("DB", "Found database match: {0}".format(result), verbosity=self.logVerbosity)
      return result[0][0]
    elif len(result) > 1:
      logzila.Log.Fatal("DB", "Database corrupted - multiple matches found in database table for: {0}".format(result))

  #################################################
  # AddSeasonDirTable
  #################################################
  def AddSeasonDirTable(self, showID, seasonNum, seasonDir):
    logzila.Log.Info("DB", "Adding season directory ({0}) to database for ShowID={1}, Season={2}".format(seasonDir, showID, seasonNum), verbosity=self.logVerbosity)

    currentValue = self.SearchSeasonDirTable(showID, seasonNum)

    if currentValue is None:
      self._QueryDatabase("INSERT INTO SeasonDir (ShowID, Season, SeasonDir) VALUES (?,?,?)", (showID, seasonNum, seasonDir))
    else:
      if currentValue == seasonDir:
        logzila.Log.Info("DB", "A matching entry already exists in the SeasonDir table", verbosity=self.logVerbosity)
      else:
        logzila.Log.Fatal("DB", "A different entry already exists in the SeasonDir table")

  #################################################
  # _PrintDatabaseTable
  # Gets database column headings using PRAGMA call
  # Automatically adjusts each column width based on the
  # longest element that needs to be printed
  #################################################
  def _PrintDatabaseTable(self, tableName):
    logzila.Log.Info("DB", "{0}".format(tableName))
    logzila.Log.IncreaseIndent()
    tableInfo = self._QueryDatabase("PRAGMA table_info({0})".format(tableName))
    tableData = self._QueryDatabase("SELECT * FROM {0}".format(tableName))

    columnCount = len(tableInfo)

    columnWidths = [0]*columnCount

    columnHeadings = []
    for count, column in enumerate(tableInfo):
      columnHeadings.append(column[1])
      columnWidths[count] = len(column[1])

    for row in tableData:
      for count, column in enumerate(row):
        if len(str(column)) > columnWidths[count]:
          columnWidths[count] = len(column)

    printStr = "|"
    for count, column in enumerate(columnWidths):
      printStr = printStr + " {{0[{0}]:{1}}} |".format(count, columnWidths[count])

    logzila.Log.Info("DB", printStr.format(columnHeadings))
    logzila.Log.Info("DB", "-"*(sum(columnWidths)+3*len(columnWidths)+1))

    for row in tableData:
      noneReplacedRow = ['-' if i is None else i for i in row]
      logzila.Log.Info("DB", printStr.format(noneReplacedRow))

    logzila.Log.DecreaseIndent()
    logzila.Log.NewLine()

  #################################################
  # PrintAllTables
  #################################################
  def PrintAllTables(self):
    logzila.Log.Info("DB", "Database contents:\n")
    for table in self._tableDict.keys():
      self._PrintDatabaseTable(table)

  #################################################
  # ManualUpdateTables
  #################################################
  def ManualUpdateTables(self):
    logzila.Log.Info("DB", "Starting manual database update:\n")

    updateFinished = False

    while not updateFinished:
      prompt = "Enter 'ls' to print the database contents, " \
                     "'a' to add a table entry, " \
                     "'d' to delete a single table row, " \
                     "'p' to select a entire table to purge, " \
                     "'f' to finish or " \
                     "'x' to exit: "
      response = logzila.Log.Input("DM", prompt)

      logzila.Log.NewLine()
      logzila.Log.IncreaseIndent()

      if response.lower() == 'x':
        logzila.Log.Fatal("DB", "Program exited by user response")
      elif response.lower() == 'f':
        updateFinished = True
      elif response.lower() == 'ls':
        self.PrintAllTables()
      elif response.lower() == 'p':
        response = logzila.Log.Input("DM", "Enter database table to purge or 'c' to cancel: ")
        if response.lower() == 'c':
          logzila.Log.Info("DB", "Database table purge cancelled")
        else:
          if response in self._tableDict.keys():
            self._PurgeTable(response)
            logzila.Log.Info("DB", "{0} database table purged".format(response))
          else:
            logzila.Log.Info("DB", "Unknown table name ({0}) given to purge".format(response))
      elif response.lower() == 'a':
        prompt = "Enter new database row (in format TABLE COL1=VAL COL2=VAL etc) " \
                  "or 'c' to cancel: "
        response = logzila.Log.Input("DM", prompt)

        if response.lower() == 'c':
          logzila.Log.Info("DB", "Database table add cancelled")
        else:
          tableName, tableColumns = response.split(' ', 1)
          if tableName not in self._tableDict.keys():
            logzila.Log.Info("DB", "Unkown table name: {0}".format(tableName))
          else:
            matchPattern = '{0}'.format(tableName)
            dbQuery = "INSERT INTO {0} (".format(tableName)
            for column in self._tableDict[tableName]:
              matchPattern = matchPattern + '\s+{0}=\s*(.+)'.format(column)
              dbQuery = dbQuery + "{0}, ".format(column)

            dbQuery = dbQuery[:-2] + ") VALUES (?{0})".format(', ?'*(len(self._tableDict[tableName])-1))
            print(dbQuery)
            try:
              match = re.findall(matchPattern, response)[0]
              print(match)
            except IndexError:
              logzila.Log.Info("DB", "Attempt to add to database table {0} failed - specified columns did not match expected".format(tableName))
            else:
              if len(self._tableDict[tableName]) > 1:
                dbTuples = match
              else:
                dbTuples = (match, )

              try:
                self._QueryDatabase(dbQuery, dbTuples)
              except sqlite3.IntegrityError:
                logzila.Log.Info("DB", "Attempt to add to database table {0} failed - check data integrity".format(tableName))
              else:
                logzila.Log.Info("DB", "Added new row to database table {0}:".format(tableName))
                self._PrintDatabaseTable(tableName)
      elif response.lower() == 'd':
        prompt = "Enter database row to delete (in format TABLE COL1=VAL COL2=VAL etc) " \
                  "or 'c' to cancel: "
        response = logzila.Log.Input("DM", prompt)

        if response.lower() == 'c':
          logzila.Log.Info("DB", "Database table row delete cancelled")
        else:
          tableName, tableColumns = response.split(' ', 1)
          if tableName not in self._tableDict.keys():
            logzila.Log.Info("DB", "Unkown table name: {0}".format(tableName))
          else:
            matchPattern = '{0}'.format(tableName)
            dbQuery = "DELETE FROM {0} WHERE".format(tableName)
            for column in self._tableDict[tableName]:
              matchPattern = matchPattern + '\s+{0}=(.+)'.format(column)
              dbQuery = dbQuery + " {0}=? AND".format(column)

            dbQuery = dbQuery[:-4]

            try:
              match = re.findall(matchPattern, response)[0]
            except IndexError:
              logzila.Log.Info("DB", "Attempt to delete row from database table {0} failed - an exact column match is required".format(tableName))
            else:
              if len(self._tableDict[tableName]) > 1:
                dbTuples = match
              else:
                dbTuples = (match, )

              self._QueryDatabase(dbQuery, dbTuples)
              logzila.Log.Info("DB", "Delete row from database table {0}:".format(tableName))
              self._PrintDatabaseTable(tableName)
      else:
        logzila.Log.Info("DB", "Unknown response")

      logzila.Log.DecreaseIndent()
      logzila.Log.NewLine()

    logzila.Log.Info("DB", "Manual database update complete.")
    self.PrintAllTables()
