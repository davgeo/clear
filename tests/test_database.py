'''

Testbench for clear.database

'''
import os
import sqlite3
import goodlogging
import unittest
import unittest.mock as mock

import clear.database

import test_lib

class ClearDatabase(unittest.TestCase):
  #################################################
  # Set up test infrastructure
  #################################################
  @classmethod
  def setUpClass(cls):
    # Silence all logging messages
    goodlogging.Log.silenceAll = True

    # Create test database at test_<RAND_STRING>.db
    cls.dbPath = test_lib.GenerateRandomPath(os.path.join(test_lib.GetBaseDir(), 'test'), '.db')
    cls.db = clear.database.RenamerDB(cls.dbPath)

  #################################################
  # Tear down test infrastructure
  #################################################
  @classmethod
  def tearDownClass(cls):
    # Delete test database
    test_lib.DeleteTestPath(cls.dbPath)

  #################################################
  # Misc database checks
  #################################################
  def test_db_MiscDatabaseCheck(self):
    # Check set up database exists
    self.assertIs(os.path.exists(self.dbPath), True)

    # Point database to a directory instead of a file path, expect fatal error
    path = test_lib.GenerateRandomPath(os.path.join(test_lib.GetBaseDir(), 'invalid_db'))
    os.mkdir(path)
    with self.assertRaises(SystemExit):
      clear.database.RenamerDB(path)
    test_lib.DeleteTestPath(path)

    # Attempt to purge a non-existant table
    with self.assertRaises(sqlite3.OperationalError):
      self.db._PurgeTable('INVALID_TABLE')

    # GetFromSingleColumnTable with non-existant table
    result = self.db._GetFromSingleColumnTable("INVALID_TABLE")
    self.assertIsNone(result)

  #################################################
  # Check Config table methods
  #################################################
  def test_db_ConfigTable(self):
    # Ensure inital Config table is empty
    result = self.db._ActionDatabase("SELECT * FROM Config", error = False)
    self.assertEqual(result, [])

    # Add config value and check it is set correctly
    self.db.SetConfigValue('TestField', 'TestValue')
    dbValue = self.db.GetConfigValue('TestField')
    self.assertEqual(dbValue, 'TestValue')

    # Update value of field
    self.db.SetConfigValue('TestField', 'TestValue2')
    dbValue = self.db.GetConfigValue('TestField')
    self.assertEqual(dbValue, 'TestValue2')

    # Try to forcibly corrupt database entry (duplicate entry for TestField)
    with self.assertRaises(sqlite3.IntegrityError):
      self.db._ActionDatabase("INSERT INTO Config VALUES (?,?)", ('TestField', 'TestValue3'))

    # Check get function on non-existant field entry
    dbValue = self.db.GetConfigValue('InvalidField')
    self.assertIsNone(dbValue)

    # Purge table and confirm
    self.db._PurgeTable('Config')
    result = self.db._ActionDatabase("SELECT * FROM Config", error = False)
    self.assertEqual(result, [])

  #################################################
  # Check SupportedFormat table methods
  #################################################
  def test_db_SupportedFormatTable(self):
    # Ensure inital SupportedFormat table is empty
    result = self.db._ActionDatabase("SELECT * FROM SupportedFormat", error = False)
    self.assertEqual(result, [])

    # Add file formats to table and check they are set correctly
    formatList = ['.testfileformat1', '.testfileformat2']
    for fileFormat in formatList:
      self.db.AddSupportedFormat(fileFormat)
    dbValue = self.db.GetSupportedFormats()
    self.assertEqual(dbValue, formatList)

    # Try to add duplicate format and check that this is ignored
    self.db.AddSupportedFormat(formatList[0])
    dbValue = self.db.GetSupportedFormats()
    self.assertEqual(dbValue, formatList)

    # Purge table and confirm
    self.db.PurgeSupportedFormats()
    dbValue = self.db.GetSupportedFormats()
    self.assertIsNone(dbValue)

  #################################################
  # Check IgnoredDir table methods
  #################################################
  def test_db_IgnoredDirTable(self):
    # Ensure inital IgnoredDir table is empty
    dbValue = self.db.GetIgnoredDirs()
    self.assertIsNone(dbValue)

    # Add directories to table and check they are set correctly
    dirList = ['ignoredir1', 'ignoredir2']
    for ignoreDir in dirList:
      self.db.AddIgnoredDir(ignoreDir)
    dbValue = self.db.GetIgnoredDirs()
    self.assertEqual(dbValue, dirList)

    # Try to add duplicate directory and check that is ignored
    self.db.AddIgnoredDir(dirList[0])
    dbValue = self.db.GetIgnoredDirs()
    self.assertEqual(dbValue, dirList)

    # Purge table and confirm
    self.db.PurgeIgnoredDirs()
    dbValue = self.db.GetIgnoredDirs()
    self.assertIsNone(dbValue)

  #################################################
  # Check TVLibrary table
  #################################################
  def test_db_TVLibraryTable(self):
    # Ensure initial TVLibrary table is empty
    result = self.db.SearchTVLibrary()
    self.assertIsNone(result)

    # Add shows to table and check show ID. Update with show directory
    showNameList = [(1, 'testshow1', 'testshowdir1'),(2, 'testshow2', 'testshowdir2')]
    for show in showNameList:
      showID = self.db.AddShowToTVLibrary(show[1])
      self.assertEqual(showID, show[0])
      self.db.UpdateShowDirInTVLibrary(showID, show[2])

    # Attempt to add duplicate showname to table, expect fatal error
    with self.assertRaises(SystemExit):
      self.db.AddShowToTVLibrary(showNameList[0][1])

    # Confirm table matches expected
    result = self.db.SearchTVLibrary()
    for count, item in enumerate(result):
      self.assertEqual(item, showNameList[count])

    # Add duplicate showDir. Expect illegal unique exception
    showID = self.db.AddShowToTVLibrary('testshow3')
    self.assertEqual(showID, 3)
    with self.assertRaises(sqlite3.IntegrityError):
      self.db.UpdateShowDirInTVLibrary(showID, showNameList[1][2])

    # Search based on showID
    result = self.db.SearchTVLibrary(showID=showNameList[0][0])
    self.assertEqual(result, [showNameList[0]])

    # Search based on showDir
    result = self.db.SearchTVLibrary(showDir=showNameList[1][2])
    self.assertEqual(result, [showNameList[1]])

    # Purge table and confirm
    self.db._PurgeTable('TVLibrary')
    result = self.db.SearchTVLibrary()
    self.assertIsNone(result)

  #################################################
  # Check FileName table
  #################################################
  def test_db_FileNameTable(self):
    # Ensure initial FileName table is empty
    result = self.db._ActionDatabase("SELECT * FROM FileName", error = False)
    self.assertEqual(result, [])

    # Add filenames to table
    fileNameList = ['filename1', 'filename2']
    for count, item in enumerate(fileNameList):
      self.db.AddToFileNameTable(item, count+1)

    # Add duplicate filename, expect fatal error
    with self.assertRaises(SystemExit):
      self.db.AddToFileNameTable(fileNameList[0], 0)

    # Check filename table matches expected
    result = self.db._ActionDatabase("SELECT * FROM FileName", error = False)
    for count, item in enumerate(result):
      self.assertEqual(item, ('filename{}'.format(count+1), count+1))

    # Check search function
    for count, item in enumerate(fileNameList):
      result = self.db.SearchFileNameTable(item)
      self.assertEqual(result, count+1)

    # Check invalid lookup
    result = self.db.SearchFileNameTable('invalidfilename')
    self.assertIsNone(result)

    # Purge table and confirm
    self.db._PurgeTable('FileName')
    result = self.db._ActionDatabase("SELECT * FROM FileName", error = False)
    self.assertEqual(result, [])

  #################################################
  # Check SeasonDir table
  #################################################
  def test_db_SeasonDirTable(self):
    # Ensure initial SeasonDir table is empty
    result = self.db._ActionDatabase("SELECT * FROM SeasonDir", error = False)
    self.assertEqual(result, [])

    # Add season directories to table and check they are set correctly
    seasonList = [(1, 1, 'Season 1'), (1, 2, 'Season 2'), (2, 5, 'Season 5')]
    for item in seasonList:
      self.db.AddSeasonDirTable(item[0], item[1], item[2])
    result = self.db._ActionDatabase("SELECT * FROM SeasonDir", error = False)
    self.assertEqual(result, seasonList)

    # Try adding a duplicate entry and check table is the same
    self.db.AddSeasonDirTable(seasonList[0][0], seasonList[0][1], seasonList[0][2])
    result = self.db._ActionDatabase("SELECT * FROM SeasonDir", error = False)
    self.assertEqual(result, seasonList)

    # Try adding a duplicate entry with different SeasonDir and check for fatal error
    with self.assertRaises(SystemExit):
      self.db.AddSeasonDirTable(seasonList[0][0], seasonList[0][1], 'Season 9')

    # Check search function
    for item in seasonList:
      result = self.db.SearchSeasonDirTable(item[0], item[1])
      self.assertEqual(result, item[2])

    # Check invalid lookup
    result = self.db.SearchSeasonDirTable(99, 99)
    self.assertIsNone(result)

    # Purge table and confirm
    self.db._PurgeTable('SeasonDir')
    result = self.db._ActionDatabase("SELECT * FROM SeasonDir", error = False)
    self.assertEqual(result, [])

  #################################################
  # Test manual update method
  # (with mocked user reponse)
  #################################################
  @mock.patch('goodlogging.Log.Input')
  def test_db_ManualUpdateTables(self, mock_input):
    # List and exit
    mock_input.side_effect = ['ls', 'x']
    with self.assertRaises(SystemExit):
      self.db.ManualUpdateTables()

    # Add to table and check
    mock_input.side_effect = ['a', 'SupportedFormat FileFormat=file.format', 'c', 'f']
    self.db.ManualUpdateTables()
    dbValue = self.db.GetSupportedFormats()
    self.assertEqual(dbValue, ['file.format'])

    # Attempt to add duplicate entry and check this is ignored
    mock_input.side_effect = ['a', 'SupportedFormat FileFormat=file.format', 'c', 'f']
    self.db.ManualUpdateTables()
    dbValue = self.db.GetSupportedFormats()
    self.assertEqual(dbValue, ['file.format'])

    # Purge table (sequence: purge-cancel-purge-no-purge-yes-finish)
    mock_input.side_effect = ['p', 'c', 'p', 'SupportedFormat', 'n', 'p', 'SupportedFormat', 'y', 'f']
    self.db.ManualUpdateTables()
    dbValue = self.db.GetSupportedFormats()
    self.assertIsNone(dbValue)

    # Attempt to purge unknown table
    mock_input.side_effect = ['p', 'UnknownTable', 'f']
    self.db.ManualUpdateTables()

    # Add to table and check
    mock_input.side_effect = ['a', 'IgnoredDir DirName=TestDir', 'c', 'f']
    self.db.ManualUpdateTables()
    dbValue = self.db.GetIgnoredDirs()
    self.assertEqual(dbValue, ['TestDir'])

    # Attempt to delete a non-existant entry, check table status is maintained
    mock_input.side_effect = ['d', 'IgnoredDir DirName=UnknownTestDir', 'y', 'c', 'f']
    self.db.ManualUpdateTables()
    dbValue = self.db.GetIgnoredDirs()
    self.assertEqual(dbValue, ['TestDir'])

    # Delete from table and check
    mock_input.side_effect = ['d', 'IgnoredDir DirName=TestDir', 'n',
                              'd', 'IgnoredDir DirName=TestDir', 'y', 'c', 'f']
    self.db.ManualUpdateTables()
    dbValue = self.db.GetIgnoredDirs()
    self.assertIsNone(dbValue)

    # Attempt to add to table with invalid format, check table is still empty
    mock_input.side_effect = ['a', 'Config Name', 'c', 'f']
    self.db.ManualUpdateTables()
    dbValue = self.db._ActionDatabase("SELECT * FROM Config")
    self.assertEqual(dbValue, [])

    # Atempt to add to non-existant table
    mock_input.side_effect = ['a', 'NonExistant TableEntry=ThisShouldntExist', 'c', 'f']
    self.db.ManualUpdateTables()

    with self.assertRaises(sqlite3.OperationalError):
      dbValue = self.db._ActionDatabase("SELECT * FROM NonExistant")

    # Attempt unknown user response
    mock_input.side_effect = ['unknowninput', 'f']
    self.db.ManualUpdateTables()

if __name__ == '__main__':
  unittest.main()
