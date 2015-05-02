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
    self._db = sqlite3.connect(dbPath)

  #################################################
  # _QueryDatabase
  #################################################
  def _QueryDatabase(self, query, tuples = None, commit = True, error = True):
    logzila.Log.Info("DB", "Database Query: {0} {1}".format(query, tuples))
    try:
      if tuples is None:
        result = self._db.execute(query)
      else:
        result = self._db.execute(query, tuples)
    except sqlite3.OperationalError:
      if error is True:
        raise
      return None
    else:
      if commit is True:
        self._db.commit()
      return result.fetchall()

  #################################################
  # _SaveAndClose
  #################################################
  def _Close(self):
    self._db.close()

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
  # AddNewShow
  #################################################
  #def AddNewShow(self, showName):
  #  dbCursor = self._dbConnection.cursor()
  #  try:
  #    dbCursor.execute("CREATE TABLE ShowName (ShowID int NOT NULL PRIMARY KEY AUTOINCREMENT, ShowName text NOT NULL)")
  #  except sqlite3.OperationalError:
  #    # Lookup existing table entry if table already exists
  #    existingTableEntry = self.GetShowID(guideName, fileShowName)
  #  else:
  #    existingTableEntry = None

  #################################################
  # _CheckAcceptableUserResponse
  #################################################
  def _CheckAcceptableUserResponse(self, response, validList):
    if response in validList:
      return response
    else:
      prompt = "Unknown response given - please reenter one of [{0}]: ".format('/'.join(validList))
      response = logzila.Log.Input("DM", prompt)
      self._CheckAcceptableUserResponse(response, validList)

  #################################################
  # AddShowNameEntry
  #################################################
  def AddShowNameEntry(self, guideName, fileShowName, guideShowName, guideID):
    tableExists = self._QueryDatabase("CREATE TABLE showname (guideName text, fileShowName text, guideShowName text, guideID int)", error = False)

    if tableExists is None:
      existingTableEntry = self.CheckShowNameTable(guideName, fileShowName)
    else:
      existingTableEntry = None

    if existingTableEntry is None:
      self._QueryDatabase("INSERT INTO showname VALUES (?,?,?,?)", (guideName, fileShowName, guideShowName, guideID))
    elif existingTableEntry[0] != guideShowName:
      logzila.Log.Info("DB", "*WARNING* Database guide show name mismatch for file show name {0}".format(fileShowName))
      logzila.Log.Info("DB", "New guide show name      = {0} (ID: {1})".format(guideShowName, guideID))
      logzila.Log.Info("DB", "Database guide show name = {0} (ID: {1})".format(existingTableEntry[0], existingTableEntry[1]))
      prompt = "Do you want to update the database with the new show name value? [y/n]: "
      response = logzila.Log.Input("DM", prompt).lower()
      self._CheckAcceptableUserResponse(response, ('y', 'n'))
      if response == 'y':
        self._QueryDatabase("UPDATE showname SET guideShowName=?, guideID=? WHERE guideName=? AND fileShowName=?", (guideShowName, guideID, guideName, fileShowName))
    elif existingTableEntry[1] != guideID:
      logzila.Log.Info("DB", "*WARNING* Database show ID mismatch for file show name {0}".format(fileShowName))
      logzila.Log.Info("DB", "New ID      = {0} (Showname: {1})".format(guideID, guideShowName))
      logzila.Log.Info("DB", "Database ID = {0} (Showname: {1})".format(existingTableEntry[1], existingTableEntry[0]))
      prompt = "Do you want to update the database with the new ID value? [y/n]: "
      response = logzila.Log.Input("DM", prompt).lower()
      self._CheckAcceptableUserResponse(response, ('y', 'n'))
      if response == 'y':
        self._QueryDatabase("UPDATE showname SET guideShowName=?, guideID=? WHERE guideName=? AND fileShowName=?", (guideShowName, guideID, guideName, fileShowName))

  #################################################
  # CheckShowNameTable
  #################################################
  def CheckShowNameTable(self, guideName, fileShowName):
    table = self._QueryDatabase("SELECT * FROM showname WHERE guideName=?", (guideName, ), error = False)

    if table is None:
      return None
    elif len(table) == 0:
      return None
    elif len(table) > 0:
      for row in table:
        if row[1].lower() == fileShowName.lower():
          return (row[2], row[3])
      return None

  #################################################
  # GetShowName
  #################################################
  def GetShowName(self, guideName, fileShowName):
    try:
      guideShowName = self.CheckShowNameTable(guideName, fileShowName)[0]
      logzila.Log.Info("DB", "Match found in database: {0}".format(fileShowName))
      return guideShowName
    except TypeError:
      return None

  #################################################
  # AddShowName
  #################################################
  def AddShowName(self, guideName, fileShowName, guideShowName):
    logzila.Log.Info("DB", "Adding match to database for future lookup {0}->{1}".format(fileShowName, guideShowName))
    self.AddShowNameEntry(guideName, fileShowName, guideShowName, 0)

  #################################################
  # GetLibraryDirectory
  #################################################
  def GetLibraryDirectory(self, showName):
    result = self._QueryDatabase("SELECT showDir FROM tv_library WHERE showName=?", (showName, ), error = False)

    if result is None:
      return None
    elif len(result) == 0:
      return None
    elif len(result) == 1:
      logzila.Log.Info("DB", "Found database match in library table {0}={1}".format(showName, result[0][0]))
      return result[0][0]

  #################################################
  # AddLibraryDirectory
  #################################################
  def AddLibraryDirectory(self, showName, showDir):
    tableExists = self._QueryDatabase("CREATE TABLE tv_library (showName text, showDir text)", error = False)

    if tableExists is None:
      currentEntry = self.GetLibraryDirectory(showName)
    else:
      currentEntry = None

    if currentEntry is None:
      logzila.Log.Info("DB", "Adding {0}={1} to database library table".format(showName, showDir))
      self._QueryDatabase("INSERT INTO tv_library VALUES (?,?)", (showName, showDir))
    else:
      logzila.Log.Info("DB", "Updating {0} in database library table from {1} to {2}".format(showName, currentEntry, showDir))
      self._QueryDatabase("UPDATE tv_library SET showDir=? WHERE showName=?", (showDir, showName))
