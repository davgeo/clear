''' DATABASE '''
# Python default package imports
import sqlite3

# Custom Python package imports

# Local file imports

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
      prompt = "  Unknown response given - please reenter one of [{0}]: ".format('/'.join(validList))
      response = input(prompt)
      self._CheckAcceptableUserResponse(response, validList)

  #################################################
  # AddShowNameEntry
  #################################################
  def AddShowNameEntry(self, fileShowName, guideShowName, guideID):
    dbCursor = self._GetCursor()
    try:
      dbCursor.execute("CREATE TABLE showname (fileName text, guideName text, guideID int)")
    except sqlite3.OperationalError:
      # Lookup existing table entry if table already exists
      existingTableEntry = self.CheckShowNameTable(fileShowName)
    else:
      existingTableEntry = None

    if existingTableEntry is None:
      dbCursor.execute("INSERT INTO showname VALUES (?,?,?)", (fileShowName, guideShowName, guideID))
    elif existingTableEntry[0] != guideShowName:
      print("*WARNING* Database guide show name mismatch for file show name {0}".format(fileShowName))
      print("            New guide show name      = {0} (ID: {1})".format(guideShowName, guideID))
      print("            Database guide show name = {0} (ID: {1})".format(existingTableEntry[0], existingTableEntry[1]))
      prompt = "  Do you want to update the database with the new show name value? [y/n]: "
      response = input(prompt).lower()
      self._CheckAcceptableUserResponse(response, ('y', 'n'))
      if response == 'y':
        dbCursor.execute("UPDATE showname SET guideName=?, guideID=? WHERE fileName=?", (guideShowName, guideID, fileShowName))
    elif existingTableEntry[1] != guideID:
      print("*WARNING* Database show ID mismatch for file show name {0}".format(fileShowName))
      print("            New ID      = {0} (Showname: {1})".format(guideID, guideShowName))
      print("            Database ID = {0} (Showname: {1})".format(existingTableEntry[1], existingTableEntry[0]))
      prompt = "  Do you want to update the database with the new ID value? [y/n]: "
      response = input(prompt).lower()
      self._CheckAcceptableUserResponse(response, ('y', 'n'))
      if response == 'y':
        dbCursor.execute("UPDATE showname SET guideName=?, guideID=? WHERE fileName=?", (guideShowName, guideID, fileShowName))
    self._CommitChanges()

  #################################################
  # CheckShowNameTable
  #################################################
  def CheckShowNameTable(self, fileShowName):
    dbCursor = self._GetCursor()
    try:
      dbCursor.execute("SELECT * FROM showname")
    except sqlite3.OperationalError:
      return None
    else:
      table = dbCursor.fetchall()
      for row in table:
        #print(row)
        if row[0].lower() == fileShowName.lower():
          return (row[1], row[2])
      return None

  #################################################
  # GetShowName
  #################################################
  def GetShowName(self, fileShowName):
    try:
      guideShowName = self.CheckShowNameTable(fileShowName)[0]
      print("  Match found in database: {0}".format(fileShowName))
      return guideShowName
    except TypeError:
      return None

  #################################################
  # AddShowName
  #################################################
  def AddShowName(self, fileShowName, guideShowName):
    print("  Adding match to database for future lookup {0}->{1}".format(fileShowName, guideShowName))
    self.AddShowNameEntry(fileShowName, guideShowName, 0)

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