'''

Testbench for clear.util

'''
import os
import shutil
import requests
import goodlogging
import unittest
import unittest.mock as mock

import clear.util

class ClearUtil(unittest.TestCase):
  #################################################
  # Set up test infrastructure:
  #################################################
  @classmethod
  def setUpClass(cls):
    # Silence all logging messages
    goodlogging.Log.silenceAll = True

  #################################################
  # Test RemoveEmptyDirectoryTree function
  #################################################
  @mock.patch('goodlogging.Log.Info')
  @mock.patch('os.path.dirname')
  @mock.patch('os.rmdir')
  def test_RemoveEmptyDirectoryTree(self, mock_rmdir, mock_dirname, mock_logging):
    mock_rmdir.side_effect = [True, OSError('Non-empty directory')]
    path = 'test/path/removal'
    result = clear.util.RemoveEmptyDirectoryTree(path, silent = False)
    self.assertEqual(mock_rmdir.call_count, 2)
    self.assertEqual(mock_logging.call_count, 3)

    # Test silent=True
    mock_rmdir.reset_mock()
    mock_logging.reset_mock()
    mock_rmdir.side_effect = [True, True, OSError('Non-empty directory')]
    result = clear.util.RemoveEmptyDirectoryTree(path, silent = True)
    self.assertEqual(mock_rmdir.call_count, 3)
    mock_logging.assert_not_called()

  #################################################
  # Test CheckPathExists function
  #################################################
  @mock.patch('os.path.exists')
  def test_CheckPathExists(self, mock_pathexists):
    path = 'test/file/path/abc.xyz'

    # Test path doesn't exist
    mock_pathexists.side_effect = [False]
    result = clear.util.CheckPathExists(path)
    self.assertEqual(result, path)

    # Test path exists
    mock_pathexists.side_effect = [True, True, False]
    result = clear.util.CheckPathExists(path)
    expectedPath = 'test/file/path/abc_2.xyz'
    self.assertEqual(result, expectedPath)

  #################################################
  # Test StripSpecialCharacters function
  #################################################
  def test_StripSpecialCharacters(self):
    # Test stripAll=False
    stringIn = '@£A$%^B*{C.:|?><DEF±§`~,/!\;= [GH] &  IJK  (X_Y-Z) "123"' + " '456' "
    expectedOut = 'ABC.DEF! [GH] and IJK (X_Y-Z) "123"' + " '456'"

    result = clear.util.StripSpecialCharacters(stringIn, stripAll = False)
    self.assertEqual(result, expectedOut)

    # Test stripAll=True
    expectedOut = 'ABCDEF![GH]andIJK(XYZ)"123"' + "'456'"
    result = clear.util.StripSpecialCharacters(stringIn, stripAll = True)
    self.assertEqual(result, expectedOut)

  #################################################
  # Test CheckEmptyResponse function
  #################################################
  @mock.patch('goodlogging.Log.Input')
  def test_CheckEmptyResponse(self, mock_input):
    # Test not empty
    notEmpty = ' This Is Not Empty '
    result = clear.util.CheckEmptyResponse(notEmpty)
    self.assertEqual(result, notEmpty)

    # Test empty
    empty = '    '
    mock_input.return_value = notEmpty
    result = clear.util.CheckEmptyResponse(empty)
    self.assertEqual(result, notEmpty)
    self.assertEqual(mock_input.call_count, 1)

  #################################################
  # Test ValidUserResponse function
  #################################################
  @mock.patch('goodlogging.Log.Input')
  def test_ValidUserResponse(self, mock_input):
    # Test valid response
    response = 'y'
    validList = ['y', 'n', 'x']

    result = clear.util.ValidUserResponse(response, validList)
    self.assertEqual(result, response)
    mock_input.assert_not_called()

    # Test invalid response
    response = 'a'
    mock_input.side_effect = ['z', 'n']
    result = clear.util.ValidUserResponse(response, validList)
    self.assertEqual(result, 'n')
    self.assertEqual(mock_input.call_count, 2)

  #################################################
  # Test UserAcceptance function
  #################################################
  @mock.patch('goodlogging.Log.Input')
  def test_UserAcceptance(self, mock_input):
    # Test single match with exit response
    matchList = ['SingleMatch']
    mock_input.side_effect = ['exit']

    with self.assertRaises(SystemExit):
      clear.util.UserAcceptance(matchList)

    # Test 'x' response
    mock_input.side_effect = ['x']
    result = clear.util.UserAcceptance(matchList)
    self.assertIsNone(result)

    # Test 'y' response
    mock_input.side_effect = ['y']
    result = clear.util.UserAcceptance(matchList)
    self.assertEqual(result, matchList[0])

    # Test multiple match list
    matchList = ['Match1', 'Match2', 'Match3']
    mock_input.side_effect = ['Match2']
    result = clear.util.UserAcceptance(matchList)
    self.assertEqual(result, 'Match2')

    # Test new lookup response (with recursiveLookup=True)
    matchList = ['Match1', 'Match2', 'Match3']
    mock_input.side_effect = ['Match4']
    result = clear.util.UserAcceptance(matchList, recursiveLookup=True)
    self.assertEqual(result, 'Match4')

    # Test new lookup response (with recursiveLookup=False)
    mock_input.reset_mock()
    matchList = ['Match1', 'Match2', 'Match3']
    mock_input.side_effect = ['Match4', 'Match5', 'Match3']
    result = clear.util.UserAcceptance(matchList, recursiveLookup=False)
    self.assertEqual(result, 'Match3')
    self.assertEqual(mock_input.call_count, 3)

    # Test empty matchList (with recursiveLookup=False)
    matchList = []
    result = clear.util.UserAcceptance(matchList, recursiveLookup=False)
    self.assertIsNone(result)

    # Test empty matchList (with recursiveLookup=True)
    matchList = []
    mock_input.side_effect = ['Match9']
    result = clear.util.UserAcceptance(matchList, recursiveLookup=True)
    self.assertEqual(result, 'Match9')

    # Test xStrOverride and prompt comment
    mock_input.reset_mock()
    xStrOverride = 'Test Override'
    promptComment = 'Test Comment'
    expectedPrompt = "Enter a different string to look up or enter 'x' {} or enter 'exit' to quit this program ({}): ".format(xStrOverride, promptComment)
    mock_input.side_effect = ['x']
    result = clear.util.UserAcceptance(matchList, xStrOverride=xStrOverride, promptComment=promptComment)
    self.assertIsNone(result)
    mock_input.assert_called_once_with('UTIL', expectedPrompt)

  #################################################
  # Test GetBestMatch function
  # Also tests GetBestStringMatchValue
  #################################################
  def test_GetBestMatch(self):
    # Test single match
    target = 'TEST'
    matchList = ['TEST', 'XYZ', 'ABC']
    result = clear.util.GetBestMatch(target, matchList)
    self.assertEqual(result, ['TEST'])

    # Test multiple match
    matchList = ['TESTA', 'XYZ', 'ABC', 'TESTB']
    result = clear.util.GetBestMatch(target, matchList)
    self.assertEqual(result, ['TESTA', 'TESTB'])

    # Test no match
    matchList = ['123', 'XYZ', 'ABC']
    result = clear.util.GetBestMatch(target, matchList)
    self.assertEqual(result, [])

    # Test empty target string
    target = ''
    result = clear.util.GetBestMatch(target, matchList)
    self.assertEqual(result, [])

  #################################################
  # Test WebLookup function
  #################################################
  @mock.patch('requests.get')
  def test_WebLookup(self, mock_requests):
    url = 'test.url'
    urlQuery = {'A': 'B'}
    webText = 'Web lookup text'

    mock_requests.return_value = mock.MagicMock(status_code=requests.codes.ok, text=webText)

    # Test successful lookup with utf8=False and urlQuery
    result = clear.util.WebLookup(url, urlQuery=urlQuery, utf8=False)
    self.assertEqual(result, webText)

    # Test successful lookup with utf8=True and no urlQuery
    clear.util.WebLookup(url, urlQuery=None, utf8=True)
    self.assertEqual(result, webText)

    # Test not okay response
    mock_requests.return_value = mock.MagicMock(status_code=requests.codes.bad)
    result = clear.util.WebLookup(url, urlQuery=None, utf8=True)
    self.assertIsNone(result)

  #################################################
  # Test ArchiveProcessedFile function
  #################################################
  @mock.patch('shutil.move')
  @mock.patch('os.makedirs')
  def test_ArchiveProcessedFile(self, mock_mkdirs, mock_move):
    filePath = 'test.file'
    archiveDir = 'ARCHIVE'

    # Test no move failure
    targetDir = os.path.join(os.path.dirname(filePath), archiveDir)
    clear.util.ArchiveProcessedFile(filePath, archiveDir)
    mock_mkdirs.assert_called_once_with(targetDir, exist_ok=True)
    mock_move.assert_called_once_with(filePath, targetDir)

    # Test move failure
    mock_mkdirs.reset_mock()
    mock_move.reset_mock()
    mock_move.side_effect = [shutil.Error('Test Shutil Error')]
    clear.util.ArchiveProcessedFile(filePath, archiveDir)
    mock_mkdirs.assert_called_once_with(targetDir, exist_ok=True)
    mock_move.assert_called_once_with(filePath, targetDir)

  #################################################
  # Test FileExtensionMatch function
  #################################################
  def test_FileExtensionMatch(self):
    filePath = 'test/file/path.file'
    supportedFileTypeList = ['.file', '.mkv', '.avi']

    # Test match
    result = clear.util.FileExtensionMatch(filePath, supportedFileTypeList)
    self.assertIs(result, True)

    # Test no match
    filePath = 'test/file/path.nomatch'
    result = clear.util.FileExtensionMatch(filePath, supportedFileTypeList)
    self.assertIs(result, False)


if __name__ == '__main__':
  unittest.main()
