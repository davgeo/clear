''' DATABASE '''
# Python default package imports
import sqlite3

# Custom Python package imports

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
    self._dbConnection = sqlite3.connect(dbPath)

  #################################################
  # _GetCursor
  #################################################
  def _GetCursor(self):
    return self._dbConnection.cursor()

  #################################################
  # _CommitChanges
  #################################################
  def _CommitChanges(self):
    self._dbConnection.commit()

  #################################################
  # _Close
  #################################################
  def _Close(self):
    self._dbConnection.close()

  #################################################
  # _SaveAndClose
  #################################################
  def _SaveAndClose(self):
    self._CommitChanges()
    self._Close()

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
    dbCursor = self._GetCursor()
    try:
      dbCursor.execute("CREATE TABLE showname (guideName text, fileShowName text, guideShowName text, guideID int)")
    except sqlite3.OperationalError:
      # Lookup existing table entry if table already exists
      existingTableEntry = self.CheckShowNameTable(guideName, fileShowName)
    else:
      existingTableEntry = None

    if existingTableEntry is None:
      dbCursor.execute("INSERT INTO showname VALUES (?,?,?,?)", (guideName, fileShowName, guideShowName, guideID))
    elif existingTableEntry[0] != guideShowName:
      logzila.Log.Info("DB", "*WARNING* Database guide show name mismatch for file show name {0}".format(fileShowName))
      logzila.Log.Info("DB", "New guide show name      = {0} (ID: {1})".format(guideShowName, guideID))
      logzila.Log.Info("DB", "Database guide show name = {0} (ID: {1})".format(existingTableEntry[0], existingTableEntry[1]))
      prompt = "Do you want to update the database with the new show name value? [y/n]: "
      response = logzila.Log.Input("DM", prompt).lower()
      self._CheckAcceptableUserResponse(response, ('y', 'n'))
      if response == 'y':
        dbCursor.execute("UPDATE showname SET guideShowName=?, guideID=? WHERE guideName=? AND fileShowName=?", (guideShowName, guideID, guideName, fileShowName))
    elif existingTableEntry[1] != guideID:
      logzila.Log.Info("DB", "*WARNING* Database show ID mismatch for file show name {0}".format(fileShowName))
      logzila.Log.Info("DB", "New ID      = {0} (Showname: {1})".format(guideID, guideShowName))
      logzila.Log.Info("DB", "Database ID = {0} (Showname: {1})".format(existingTableEntry[1], existingTableEntry[0]))
      prompt = "Do you want to update the database with the new ID value? [y/n]: "
      response = logzila.Log.Input("DM", prompt).lower()
      self._CheckAcceptableUserResponse(response, ('y', 'n'))
      if response == 'y':
        dbCursor.execute("UPDATE showname SET guideShowName=?, guideID=? WHERE guideName=? AND fileShowName=?", (guideShowName, guideID, guideName, fileShowName))
    self._CommitChanges()

  #################################################
  # CheckShowNameTable
  #################################################
  def CheckShowNameTable(self, guideName, fileShowName):
    dbCursor = self._GetCursor()
    try:
      dbCursor.execute("SELECT * FROM showname WHERE guideName=?", (guideName, ))
    except sqlite3.OperationalError:
      return None
    else:
      table = dbCursor.fetchall()
      for row in table:
        #print(row)
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
  # GetConfigValue
  #################################################
  def GetConfigValue(self, fieldName):
    dbCursor = self._GetCursor()
    try:
      dbCursor.execute("SELECT value FROM config WHERE name=?", (fieldName, ))
    except sqlite3.OperationalError:
      return None
    else:
      value = dbCursor.fetchone()
      if value is None:
        return None
      else:
        value = value[0]
      logzila.Log.Info("DB", "Found database match in config table {0}={1}".format(fieldName, value))
      return value

  #################################################
  # SetConfigValue
  #################################################
  def SetConfigValue(self, fieldName, value):
    dbCursor = self._GetCursor()
    try:
      dbCursor.execute("CREATE TABLE config (name text, value text)")
    except sqlite3.OperationalError:
      currentEntry = self.GetConfigValue(fieldName)
    else:
      currentEntry = None

    if currentEntry is None:
      logzila.Log.Info("DB", "Adding {0}={1} to database config table".format(fieldName, value))
      dbCursor.execute("INSERT INTO config VALUES (?,?)", (fieldName, value))
    else:
      logzila.Log.Info("DB", "Updating {0} in database config table from {1} to {2}".format(fieldName, currentEntry, value))
      dbCursor.execute("UPDATE config SET value=?, WHERE name=?", (value, fieldName))
    self._CommitChanges()

  #################################################
  # GetSupportedFormats
  #################################################
  def GetSupportedFormats(self):
    dbCursor = self._GetCursor()
    try:
      dbCursor.execute("SELECT * FROM supported_formats")
    except sqlite3.OperationalError:
      return None
    else:
      table = dbCursor.fetchall()
      formatList = [i[0] for i in table]
      return formatList

  #################################################
  # AddSupportedFormat
  #################################################
  def AddSupportedFormat(self, fileFormat):
    fileFormat = fileFormat.lower()
    match = None
    dbCursor = self._GetCursor()
    try:
      dbCursor.execute("CREATE TABLE supported_formats (name text)")
    except sqlite3.OperationalError:
      currentFormats = self.GetSupportedFormats()
      if currentFormats is not None:
        for item in currentFormats:
          if item == fileFormat:
            match = 1

    if match is None:
      logzila.Log.Info("DB", "Adding {0} to supported formats table".format(fileFormat))
      dbCursor.execute("INSERT INTO supported_formats VALUES (?)", (fileFormat, ))
    else:
      logzila.Log.Info("DB", "{0} already exists in supported formats table".format(fileFormat))
    self._CommitChanges()

  #################################################
  # GetIgnoredDirs
  #################################################
  def GetIgnoredDirs(self):
    dbCursor = self._GetCursor()
    try:
      dbCursor.execute("SELECT * FROM ignored_dirs")
    except sqlite3.OperationalError:
      return None
    else:
      table = dbCursor.fetchall()
      dirList = [i[0] for i in table]
      return dirList

  #################################################
  # AddIgnoredDir
  #################################################
  def AddIgnoredDir(self, ignoredDir):
    print(ignoredDir)
    match = None
    dbCursor = self._GetCursor()
    try:
      dbCursor.execute("CREATE TABLE ignored_dirs (name text)")
    except sqlite3.OperationalError:
      ignoredDirList = self.GetIgnoredDirs()
      print("ignoredDirList = {0}".format(ignoredDirList))
      if ignoredDirList is not None:
        for item in ignoredDirList:
          if item == ignoredDir:
            match = 1

    if match is None:
      logzila.Log.Info("DB", "Adding {0} to ignored directories table".format(ignoredDir))
      dbCursor.execute("INSERT INTO ignored_dirs VALUES (?)", (ignoredDir, ))
    else:
      logzila.Log.Info("DB", "{0} already exists in ignored directories table".format(ignoredDir))
    self._CommitChanges()

  #################################################
  # DropTable
  #################################################
  def DropTable(self, tableName):
    logzila.Log.Info("DB", "Deleting table {0}".format(tableName))
    dbCursor = self._GetCursor()
    try:
      dbCursor.execute("DROP TABLE {0}".format(tableName))
    except sqlite3.OperationalError:
      pass

  #################################################
  # Test
  #################################################
  def Test(self):
    #print(self.CheckShowNameTable('TopGearUK02'))
    self.AddShowNameEntry('TopGearUK02', 'Top Gear (UK : 2002)', 6549)
    #self.AddShowNameEntry('TopGearUK02', 'Top Gear (US)', 7921)
    print(self.CheckShowNameTable('TopGearUK02'))
    self._SaveAndClose()

############################################################################
# main
############################################################################
def main():
  db = RenamerDB('example.test')
  db.Test()

############################################################################
# default process if run as standalone
############################################################################
if __name__ == "__main__":
  main()