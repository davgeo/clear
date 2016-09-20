'''

Testbench for clear.renamer

'''
import os
import errno
import shutil
import goodlogging
import unittest
import unittest.mock as mock

import clear.renamer

class Clear(unittest.TestCase):
  #################################################
  # Set up test infrastructure
  #################################################
  @classmethod
  def setUpClass(cls):
    # Silence all logging messages
    goodlogging.Log.silenceAll = True

  #################################################
  # Test _SetGuide function
  #################################################
  def test_renamer_SetGuide(self):
    renamer = clear.renamer.TVRenamer('fakedb', 'fakelist', 'fakedir')
    self.assertIsInstance(renamer._guide, clear.epguides.EPGuidesLookup)

    # Test invalid guide name
    with self.assertRaises(Exception):
      renamer = clear.renamer.TVRenamer('fakedb', 'fakelist', 'fakedir', guideName='error')

  #################################################
  # Test _GetUniqueFileShowNames function
  #################################################
  def test_renamer_GetUniqueFileShowNames(self):
    tvFileList = []
    unique_list = ['TestShowName1', 'TestShowName2', 'TestShowName3']
    showname_list = unique_list + ['TestShowName1', 'TestShowName3']

    for name in showname_list:
      fileInfoObj = mock.MagicMock(showName=name)
      tvFileObj = mock.MagicMock(fileInfo=fileInfoObj)
      tvFileList.append(tvFileObj)

    renamer = clear.renamer.TVRenamer('fakedb', tvFileList, 'fakedir')
    result = renamer._GetUniqueFileShowNames(tvFileList)
    self.assertEqual(sorted(list(result)), sorted(unique_list))

  #################################################
  # Test _GetShowID function
  #################################################
  @mock.patch('goodlogging.Log.Input')
  @mock.patch('clear.util.UserAcceptance')
  @mock.patch('clear.epguides.EPGuidesLookup', autospec=True)
  @mock.patch('clear.database.RenamerDB', autospec=True)
  def test_renamer_GetShowID(self, mock_db, mock_guide, mock_useraccept, mock_input):
    db = mock_db.return_value
    guide = mock_guide.return_value
    renamer = clear.renamer.TVRenamer(db, 'fakelist', 'fakedir', guideName=clear.epguides.EPGuidesLookup.GUIDE_NAME)

    # Find ShowID in database via exact match of show name
    stringSearch = 'fakeshowfilename'
    showID = '10'
    db.SearchFileNameTable.return_value = showID
    result = renamer._GetShowID(stringSearch)
    self.assertEqual(result.showID, showID)
    self.assertIs(db.AddToFileNameTable.called, False)

    # Cannot find show name in database - lookup exact show name in guide then check database for ShowID entry
    db.SearchFileNameTable.return_value = None
    guide.ShowNameLookUp.return_value = ['Fake Show 1', 'Fake Show 2', 'Fake Show 3']

    # User cancels show name acceptance
    mock_useraccept.return_value = None
    result = renamer._GetShowID(stringSearch)
    self.assertIsNone(result)

    # Show name match found in guide
    mock_useraccept.return_value = 'Fake Show 2'

    # ShowID match found in TVLibrary
    showID = '11'
    db.SearchTVLibrary.return_value = [[showID, 'Fake Show 2']]
    result = renamer._GetShowID(stringSearch)
    self.assertEqual(result.showID, showID)
    db.SearchTVLibrary.assert_called_once_with('Fake Show 2')

    # Show name match found with empty TV library (new ShowID created from AddShowToTVLibrary)
    db.AddToFileNameTable.reset_mock()
    showID = '12'
    db.AddShowToTVLibrary.return_value = showID
    db.SearchTVLibrary.return_value = None
    mock_input.return_value = 'ls'
    result = renamer._GetShowID(stringSearch)
    self.assertEqual(result.showID, showID)
    self.assertEqual(db.AddShowToTVLibrary.call_count, 1)
    self.assertEqual(db.AddToFileNameTable.call_count, 1)
    self.assertEqual(mock_input.call_count, 1)

    # Show name match found but no match in TV library (new show - create new ShowID again)
    db.SearchTVLibrary.side_effect = [None, [['13', 'Fake Show 5'], ['14', 'Fake Show 6']]]
    mock_input.side_effect = ['ls', 'y']
    showID = '13'
    db.AddShowToTVLibrary.return_value = showID
    result = renamer._GetShowID(stringSearch)
    self.assertEqual(result.showID, showID)
    self.assertEqual(db.AddShowToTVLibrary.call_count, 2)
    self.assertEqual(db.AddToFileNameTable.call_count, 2)
    self.assertEqual(mock_input.call_count, 3)

    # Show name match found, match found in TV library (not a new show)
    showID = '15'
    db.SearchTVLibrary.side_effect = [None, [[showID, 'Fake Show 2'], ['16', 'Fake Show 6']], [[showID, 'Fake Show 2']]]
    mock_input.side_effect = ['ls', 'n']
    result = renamer._GetShowID(stringSearch)
    self.assertEqual(result.showID, showID)

    # Previous test without 'ls' input step
    showID = '17'
    db.SearchTVLibrary.side_effect = [None, [[showID, 'Fake Show 2'], ['16', 'Fake Show 6']], [[showID, 'Fake Show 2']]]
    mock_input.side_effect = ['n']
    result = renamer._GetShowID(stringSearch)
    self.assertEqual(result.showID, showID)

    # Previous test with empty TVLibrary
    showID = '18'
    db.SearchTVLibrary.side_effect = [None, None]
    mock_input.side_effect = ['n']
    result = renamer._GetShowID(stringSearch)
    self.assertIsNone(result)

    # As previous tests but ShowID lookup in library cancelled by user (non-empty TVLibrary)
    mock_useraccept.side_effect = ['Fake Show 2', None]
    db.SearchTVLibrary.side_effect = [None, [[showID, 'Fake Show 2'], ['16', 'Fake Show 6']]]
    mock_input.side_effect = ['n']
    result = renamer._GetShowID(stringSearch)
    self.assertIsNone(result)

    # Recursive call test (Look up user given show name)
    showID = '19'
    db.AddShowToTVLibrary.return_value = showID
    mock_useraccept.side_effect = ['Fake Show Not Found', 'Fake Show 2']
    db.SearchTVLibrary.side_effect = [None, [[showID, 'Fake Show 2'], ['16', 'Fake Show 6']]]
    mock_input.side_effect = ['y']
    result = renamer._GetShowID(stringSearch)
    self.assertEqual(result.showID, showID)

    # Previous test except second iteration matches database
    showID = '20'
    db.AddShowToTVLibrary.return_value = showID
    db.SearchFileNameTable.side_effect = [None, showID]
    mock_useraccept.side_effect = ['Fake Show Not Found', 'Fake Show 2']
    db.SearchTVLibrary.side_effect = [None, [[showID, 'Fake Show 2'], ['16', 'Fake Show 6']]]
    mock_input.side_effect = ['y']
    result = renamer._GetShowID(stringSearch)
    self.assertEqual(result.showID, showID)

    # Test skipUserInput=True
    showID = '21'
    renamer._skipUserInput = True
    db.SearchFileNameTable.side_effect = None
    result = renamer._GetShowID(stringSearch)
    self.assertIsNone(result)

    # As previous test except with single match from guide
    showID = '22'
    db.AddShowToTVLibrary.return_value = showID
    guide.ShowNameLookUp.return_value = ['Fake Show 2']
    db.SearchTVLibrary.side_effect = None
    result = renamer._GetShowID(stringSearch)
    self.assertEqual(result.showID, showID)

  #################################################
  # Test _GetShowInfo function
  #################################################
  @mock.patch('clear.renamer.TVRenamer._GetShowID')
  @mock.patch('clear.database.RenamerDB', autospec=True)
  def test_renamer_GetShowInfo(self, mock_db, mock_getshowid):
    db = mock_db.return_value
    renamer = clear.renamer.TVRenamer(db, 'fakelist', 'fakedir')

    testFile = mock.MagicMock(showID='5', showName='Test')
    mock_getshowid.return_value = testFile
    result = renamer._GetShowInfo('TestStringSearch')
    self.assertEqual(result.showID, testFile.showID)
    self.assertEqual(result.showName, testFile.showName)

    testFile = mock.MagicMock(showID='6', showName=None)
    mock_getshowid.return_value = testFile
    db.SearchTVLibrary.side_effect = [[['6', 'TestLookup']]]
    result = renamer._GetShowInfo('TestStringSearch')
    self.assertEqual(result.showID, testFile.showID)
    self.assertEqual(result.showName, 'TestLookup')

    testFile = mock.MagicMock(showID=None, showName='Test2')
    mock_getshowid.return_value = testFile
    result = renamer._GetShowInfo('TestStringSearch')
    self.assertIsNone(result)

    testFile = None
    mock_getshowid.return_value = testFile
    result = renamer._GetShowInfo('TestStringSearch')
    self.assertIsNone(result)

  #################################################
  # Test _MoveFileToLibrary function
  #################################################
  @mock.patch('clear.util.CheckPathExists')
  @mock.patch('clear.util.ArchiveProcessedFile')
  @mock.patch('shutil.copy2')
  @mock.patch('os.rename')
  @mock.patch('os.path.exists')
  @mock.patch('os.makedirs')
  def test_renamer_MoveFileToLibrary(self, mock_makedirs, mock_pathexists, mock_rename,
                                    mock_copy, mock_archivefile, mock_utilcheck):
    renamer = clear.renamer.TVRenamer('fakedir', 'fakelist', 'fakedir')

    # Test old path equals new path
    oldPath = 'this/path.file'
    result = renamer._MoveFileToLibrary(oldPath, oldPath)
    self.assertIs(result, False)

    # Test old path equals new path
    mock_pathexists.return_value = True
    oldPath = 'this/old/path/old.file'
    newPath = 'this/new/path/new.file'
    result = renamer._MoveFileToLibrary(oldPath, newPath)
    self.assertIs(result, False)

    # Test straightforward rename
    mock_pathexists.return_value = False
    result = renamer._MoveFileToLibrary(oldPath, newPath)
    mock_rename.assert_called_once_with(oldPath, newPath)
    self.assertIs(result, True)

    # Test miscellaneous exception on rename
    mock_rename.side_effect = Exception('TEST EXCEPTION', 'Unknown test exception message')
    result = renamer._MoveFileToLibrary(oldPath, newPath)
    self.assertIsNot(result, True)

    # Test miscellaneous OSError exception
    mock_rename.side_effect = OSError('TEST OSError', 'Unknown test exception message')
    result = renamer._MoveFileToLibrary(oldPath, newPath)
    self.assertIsNot(result, True)

    # Test different file system exception with disabled copy
    mock_rename.side_effect = [OSError(errno.EXDEV, 'EXDEV Error'), True]
    renamePath = 'this/old/path/new.file'
    checkPath = '{}2'.format(renamePath)
    mock_utilcheck.return_value = checkPath
    result = renamer._MoveFileToLibrary(oldPath, newPath)
    mock_utilcheck.assert_called_once_with(renamePath)
    mock_copy.assert_not_called()
    self.assertIsNot(result, True)

    # As above except new and old path share the same file name
    mock_rename.side_effect = [OSError(errno.EXDEV, 'EXDEV Error'), True]
    oldPath = 'this/old/path/new.file'
    mock_utilcheck.reset_mock()
    result = renamer._MoveFileToLibrary(oldPath, newPath)
    mock_utilcheck.assert_not_called()
    mock_copy.assert_not_called()
    self.assertIsNot(result, True)

    # Test different file system exception with enabled copy
    oldPath = 'this/old/path/old.file'
    renamer._forceCopy = True
    mock_rename.side_effect = [OSError(errno.EXDEV, 'EXDEV Error'), True]
    result = renamer._MoveFileToLibrary(oldPath, newPath)
    mock_copy.assert_called_once_with(checkPath, newPath)
    self.assertIs(result, True)

    # As above except second rename also hits exception
    mock_rename.side_effect = [OSError(errno.EXDEV, 'EXDEV Error'),
                               Exception('TEST EXCEPTION', 'Unknown test exception message')]
    result = renamer._MoveFileToLibrary(oldPath, newPath)
    self.assertIsNot(result, True)

    # Test shutil copy throws exception
    mock_copy.reset_mock()
    mock_rename.side_effect = [OSError(errno.EXDEV, 'EXDEV Error'), True]
    mock_copy.side_effect = shutil.Error('SHUTIL ERR', 'Shutil error message')
    result = renamer._MoveFileToLibrary(oldPath, newPath)
    mock_copy.assert_called_once_with(checkPath, newPath)
    self.assertIsNot(result, True)

  #################################################
  # Test _CreateNewSeasonDir function
  #################################################
  @mock.patch('goodlogging.Log.Input')
  def test_renamer_CreateNewSeasonDir(self, mock_input):
    renamer = clear.renamer.TVRenamer('fakedb', 'fakelist', 'fakedir')
    seasonNum = 5

    # Test user reponse 'y'
    mock_input.side_effect = ['y']
    expectedResult = "Season {0}".format(seasonNum)
    result = renamer._CreateNewSeasonDir(seasonNum)
    self.assertEqual(result, expectedResult)

    # Test user reponse 'b'
    mock_input.side_effect = ['b']
    expectedResult = ''
    result = renamer._CreateNewSeasonDir(seasonNum)
    self.assertEqual(result, expectedResult)

    # Test user reponse 'x'
    mock_input.side_effect = ['x']
    expectedResult = None
    result = renamer._CreateNewSeasonDir(seasonNum)
    self.assertEqual(result, expectedResult)

    # Test user reponse new season directory
    expectedResult = "CustomSeasonDir {0}".format(seasonNum)
    mock_input.side_effect = [expectedResult]
    result = renamer._CreateNewSeasonDir(seasonNum)
    self.assertEqual(result, expectedResult)

    # Test empty response
    mock_input.reset_mock()
    expectedResult = "CustomSeasonDir {0}".format(seasonNum)
    mock_input.side_effect = ['', expectedResult]
    result = renamer._CreateNewSeasonDir(seasonNum)
    self.assertEqual(result, expectedResult)
    self.assertEqual(mock_input.call_count, 2)

    # Test without skip user input
    mock_input.reset_mock()
    renamer._skipUserInput = True
    expectedResult = "Season {0}".format(seasonNum)
    result = renamer._CreateNewSeasonDir(seasonNum)
    self.assertEqual(result, expectedResult)
    mock_input.assert_not_called()

  #################################################
  # Test _LookUpSeasonDirectory function
  #################################################
  @mock.patch('clear.util.UserAcceptance')
  @mock.patch('os.listdir')
  @mock.patch('clear.renamer.TVRenamer._CreateNewSeasonDir')
  @mock.patch('os.path.isdir')
  @mock.patch('clear.database.RenamerDB', autospec=True)
  def test_renamer_LookUpSeasonDirectory(self, mock_db, mock_isdir, mock_createdir, mock_listdir,
                                         mock_useraccept):
    db = mock_db.return_value
    renamer = clear.renamer.TVRenamer(db, 'fakelist', 'fakedir')

    seasonDirName = 'Test Season X'

    showID = '123'
    showDir = 'Test Show Dir'
    seasonNum = '5'

    # Get season directory match from database table
    db.SearchSeasonDirTable.return_value = seasonDirName
    result = renamer._LookUpSeasonDirectory(showID, showDir, seasonNum)
    self.assertEqual(result, seasonDirName)
    db.SearchSeasonDirTable.assert_called_once_with(showID, seasonNum)
    mock_isdir.assert_not_called()

    # No match found in database
    db.SearchSeasonDirTable.return_value = None

    # Test show directory does not exist (create new directory)
    mock_isdir.return_value = False
    expectedResult = 'CreatedSeasonDir'
    mock_createdir.return_value = expectedResult
    result = renamer._LookUpSeasonDirectory(showID, showDir, seasonNum)
    self.assertEqual(result, expectedResult)
    db.AddSeasonDirTable.assert_called_once_with(showID, seasonNum, result)

    # Show directory exists but is empty
    db.AddSeasonDirTable.reset_mock()
    mock_isdir.return_value = True
    mock_listdir.return_value = []
    mock_useraccept.return_value = None
    result = renamer._LookUpSeasonDirectory(showID, showDir, seasonNum)
    self.assertEqual(result, expectedResult)
    self.assertIs(mock_useraccept.called, True)
    db.AddSeasonDirTable.assert_called_once_with(showID, seasonNum, result)

    # Test non-empty show directory with single match
    db.AddSeasonDirTable.reset_mock()
    mock_isdir.return_value = True
    expectedResult = 'Season 05'
    mock_listdir.return_value = ['Season 01', 'Season 2', 'Season 6', expectedResult]
    mock_useraccept.side_effect = [expectedResult]
    result = renamer._LookUpSeasonDirectory(showID, showDir, seasonNum)
    self.assertEqual(result, expectedResult)
    db.AddSeasonDirTable.assert_called_once_with(showID, seasonNum, result)

    # Test non-empty show directory with multiple match
    db.AddSeasonDirTable.reset_mock()
    mock_isdir.return_value = True
    expectedResult = 'Season 05'
    mock_listdir.return_value = ['Season 01', 'Season 2', 'Season 6', 'Season 5', expectedResult]
    mock_useraccept.side_effect = [expectedResult]
    result = renamer._LookUpSeasonDirectory(showID, showDir, seasonNum)
    self.assertEqual(result, expectedResult)
    db.AddSeasonDirTable.assert_called_once_with(showID, seasonNum, result)

    # Test recursive lookup, start with list directory
    db.AddSeasonDirTable.reset_mock()
    mock_isdir.return_value = True
    expectedResult = 'Season Five'
    mock_listdir.return_value = ['Season 01', 'Season 2', 'Season 6', expectedResult]
    mock_useraccept.side_effect = ['ls', expectedResult, expectedResult]
    result = renamer._LookUpSeasonDirectory(showID, showDir, seasonNum)
    self.assertEqual(result, expectedResult)
    db.AddSeasonDirTable.assert_called_once_with(showID, seasonNum, result)

    # Test list directory with empty response
    db.AddSeasonDirTable.reset_mock()
    mock_createdir.reset_mock()
    mock_isdir.return_value = True
    expectedResult = 'CreatedSeasonDir'
    mock_createdir.return_value = expectedResult
    mock_listdir.return_value = []
    mock_useraccept.side_effect = ['ls', 'S.Five', 'S5', None]
    result = renamer._LookUpSeasonDirectory(showID, showDir, seasonNum)
    self.assertEqual(result, expectedResult)
    db.AddSeasonDirTable.assert_called_once_with(showID, seasonNum, result)
    self.assertIs(mock_createdir.called, True)

    # Test skipUserInput=True with single match
    renamer._skipUserInput=True
    db.AddSeasonDirTable.reset_mock()
    mock_useraccept.reset_mock()
    mock_isdir.return_value = True
    expectedResult = 'Season 05'
    mock_listdir.return_value = ['Season 01', 'Season 2', 'Season 6', expectedResult]
    result = renamer._LookUpSeasonDirectory(showID, showDir, seasonNum)
    self.assertEqual(result, expectedResult)
    db.AddSeasonDirTable.assert_called_once_with(showID, seasonNum, result)
    mock_useraccept.assert_not_called()

    # Test skipUserInput=True with multiple matches
    db.AddSeasonDirTable.reset_mock()
    mock_isdir.return_value = True
    expectedResult = 'CreatedSeasonDir'
    mock_createdir.return_value = expectedResult
    mock_listdir.return_value = ['Season 01', 'Season 2', 'Season 6', 'Season 5', 'Season 05']
    result = renamer._LookUpSeasonDirectory(showID, showDir, seasonNum)
    self.assertEqual(result, expectedResult)
    db.AddSeasonDirTable.assert_called_once_with(showID, seasonNum, result)
    mock_useraccept.assert_not_called()

  #################################################
  # Test _CreateNewShowDir function
  #################################################
  @mock.patch('clear.util.StripSpecialCharacters')
  @mock.patch('goodlogging.Log.Input')
  def test_renamer_CreateNewShowDir(self, mock_input, mock_strip):
    renamer = clear.renamer.TVRenamer('fakedir', 'fakelist', 'fakedir')

    showName = 'This.New.Show.Name.2016'

    # Test user reponse 'y'
    mock_input.side_effect = ['y']
    expectedResult = 'ThisNewShowName'
    mock_strip.side_effect = [expectedResult]
    result = renamer._CreateNewShowDir(showName)
    self.assertEqual(result, expectedResult)

    # Test user reponse 'x'
    mock_input.side_effect = ['x']
    mock_strip.side_effect = [expectedResult]
    result = renamer._CreateNewShowDir(showName)
    self.assertIsNone(result)

    # Test user reponse new show name
    customShowName = 'ShowName'
    stripedResult = 'ThisNewShowName'
    mock_input.side_effect = [customShowName]
    mock_strip.side_effect = [stripedResult]
    result = renamer._CreateNewShowDir(showName)
    self.assertEqual(result, customShowName)

    # Test empty string response for using base directory
    customShowName = ''
    stripedResult = 'ThisNewShowName'
    mock_input.side_effect = [customShowName]
    mock_strip.side_effect = [stripedResult]
    result = renamer._CreateNewShowDir(showName)
    self.assertEqual(result, customShowName)

    # Test skipUserInput=True
    mock_input.reset_mock()
    renamer._skipUserInput = True
    expectedResult = 'ThisNewShowName'
    mock_strip.side_effect = [expectedResult]
    result = renamer._CreateNewShowDir(showName)
    self.assertEqual(result, expectedResult)
    mock_input.assert_not_called()

  #################################################
  # Test _GenerateLibraryPath function
  #################################################
  @mock.patch('os.listdir')
  @mock.patch('clear.util.UserAcceptance')
  @mock.patch('clear.util.GetBestMatch')
  @mock.patch('clear.renamer.TVRenamer._LookUpSeasonDirectory')
  @mock.patch('clear.renamer.TVRenamer._CreateNewShowDir')
  @mock.patch('clear.database.RenamerDB', autospec=True)
  def test_renamer_GenerateLibraryPath(self, mock_db, mock_createshowdir, mock_seasonlookup, mock_getbestmatch,
                                        mock_userinput, mock_lsdir):
    db = mock_db.return_value
    renamer = clear.renamer.TVRenamer(db, 'fakelist', 'fakedir')

    (showID, showName, showDir, seasonNum) = ('7', 'SevenShow', 'SevenShowDir', '9')
    db.SearchTVLibrary.return_value = ((showID, showName, showDir),)

    tvFile = mock.MagicMock(spec=clear.tvfile.TVFile)
    tvFile.showInfo = mock.MagicMock(showName=showName, seasonNum=seasonNum)
    libraryDir = 'fakelibraryDir'

    # Test db match show directory no season directory found
    mock_seasonlookup.return_value = None
    result = renamer._GenerateLibraryPath(tvFile, libraryDir)
    self.assertEqual(result.showInfo.showName, showName)
    self.assertIs(tvFile.GenerateNewFilePath.called, False)

    # Test db match show directory with season directory found
    seasonDir = 'Season 9'
    mock_seasonlookup.return_value = seasonDir
    result = renamer._GenerateLibraryPath(tvFile, libraryDir)
    self.assertEqual(result.showInfo.showName, showName)
    self.assertIs(tvFile.GenerateNewFilePath.called, True)

    # Test empty list dir, and cancelled create show dir
    mock_seasonlookup.reset_mock()
    mock_seasonlookup.return_value = None
    mock_lsdir.return_value = []
    mock_createshowdir.return_value = None
    db.SearchTVLibrary.return_value = ((showID, showName, None),)
    result = renamer._GenerateLibraryPath(tvFile, libraryDir)
    self.assertEqual(result.showInfo.showName, showName)
    mock_createshowdir.assert_called_once_with(showName)
    mock_seasonlookup.assert_not_called()

    # Test non-empty list dir
    showDir = 'Show7'
    mock_lsdir.return_value = ['ShowA', 'ShowB', showDir, 'Show72']
    mock_getbestmatch.side_effect = [[], [showDir, 'Show72']]
    mock_userinput.side_effect = ['ls', showDir, showDir]
    result = renamer._GenerateLibraryPath(tvFile, libraryDir)
    self.assertEqual(result.showInfo.showName, showName)
    mock_seasonlookup.assert_called_once_with(showID, os.path.join(libraryDir, showDir), seasonNum)
    db.UpdateShowDirInTVLibrary.assert_called_once_with(showID, showDir)

    # Test skipUserInput=True. Multiple entry match (create new directory)
    renamer._skipUserInput = True
    mock_userinput.reset_mock()
    mock_seasonlookup.reset_mock()
    db.UpdateShowDirInTVLibrary.reset_mock()
    mock_createshowdir.reset_mock()
    mock_getbestmatch.side_effect = [[showDir, 'Show72']]
    createdShowDir = 'SevenShow'
    mock_createshowdir.return_value = createdShowDir
    result = renamer._GenerateLibraryPath(tvFile, libraryDir)
    self.assertEqual(result.showInfo.showName, showName)
    mock_seasonlookup.assert_called_once_with(showID, os.path.join(libraryDir, createdShowDir), seasonNum)
    db.UpdateShowDirInTVLibrary.assert_called_once_with(showID, createdShowDir)
    mock_createshowdir.assert_called_once_with(showName)
    mock_userinput.assert_not_called()

    # Test skipUserInput=True. Single entry match.
    mock_userinput.reset_mock()
    mock_seasonlookup.reset_mock()
    db.UpdateShowDirInTVLibrary.reset_mock()
    mock_createshowdir.reset_mock()
    mock_getbestmatch.side_effect = [[showDir]]
    result = renamer._GenerateLibraryPath(tvFile, libraryDir)
    self.assertEqual(result.showInfo.showName, showName)
    mock_seasonlookup.assert_called_once_with(showID, os.path.join(libraryDir, showDir), seasonNum)
    db.UpdateShowDirInTVLibrary.assert_called_once_with(showID, showDir)
    mock_createshowdir.assert_not_called()
    mock_userinput.assert_not_called()

  #################################################
  # Test Run function
  #################################################
  def test_renamer_Run(self):
    goodlogging.Log.silenceAll = False
    goodlogging.Log.silenceAll = True



if __name__ == '__main__':
  unittest.main()
