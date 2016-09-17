'''

Testbench for clear.extract

'''
import goodlogging
import rarfile
import unittest
import unittest.mock as mock

import test_lib

import clear.extract

class Extract(unittest.TestCase):
  #################################################
  # Set up test infrastructure:
  #################################################
  @classmethod
  def setUpClass(cls):
    # Silence all logging messages
    goodlogging.Log.silenceAll = True

  #################################################
  # Test GetCompressedFilesInDir function
  #################################################
  @mock.patch('glob.glob')
  @mock.patch('os.path.isdir')
  def test_extract_GetCompressedFilesInDir(self, mock_isdir, mock_glob):
    fileList = []
    fileDir = 'fake/path'
    ignoreDirList = ''
    supportedFormatList = ['.rar',]

    # Check file directory is not a directory
    mock_isdir.return_value = False
    clear.extract.GetCompressedFilesInDir(fileDir, fileList, ignoreDirList, supportedFormatList)
    self.assertEqual(fileList, [])

    # Force isdir to resolve true
    mock_isdir.return_value = True
    mock_glob.return_value = ['testfile1.txt', 'testfile2.rar', 'testfile3.zip', 'testdir4']
    expectedFileList = ['testfile2.rar']
    clear.extract.GetCompressedFilesInDir(fileDir, fileList, ignoreDirList, supportedFormatList)
    self.assertEqual(fileList, expectedFileList)

    # Check more complex glob paths
    mock_glob.return_value = ['this/path/testfile5.txt',
                              'this/path/testfile6.rar',
                              'this/path/testdir7']
    expectedFileList.append('this/path/testfile6.rar')
    clear.extract.GetCompressedFilesInDir(fileDir, fileList, ignoreDirList, supportedFormatList)
    self.assertEqual(fileList, expectedFileList)

  #################################################
  # Test MultipartArchiving function
  #################################################
  @mock.patch('clear.util.ArchiveProcessedFile')
  def test_extract_MultipartArchiving(self, mock_util):
    firstPartExtractList = []
    otherPartSkippedList = ['file1.part3.rar']
    archiveDir = 'fakedir'

    # Mock of util.ArchiveProcessedFile will do nothing and return True
    mock_util.return_value = True

    # Found new parts but first part not extracted yet
    otherPartExtractionList = ['file1.part2.rar', 'file1.part3.rar', 'file1.part4.rar']
    for otherPartFilePath in otherPartExtractionList:
      clear.extract.MultipartArchiving(firstPartExtractList, otherPartSkippedList, archiveDir, otherPartFilePath)
    self.assertEqual(sorted(otherPartSkippedList), sorted(otherPartExtractionList))

    # Found new parts with first part previously extracted
    firstPartExtractList = 'file1.part1.rar'
    for otherPartFilePath in otherPartExtractionList:
      clear.extract.MultipartArchiving(firstPartExtractList, otherPartSkippedList, archiveDir, otherPartFilePath)
    self.assertEqual(otherPartSkippedList, [])

    # End of extraction reached. Call function to scan through remaining parts and archive as appropriate
    extractedPartList = ['file1.part2.rar', 'file1.part3.rar', 'file1.part4.rar']
    nonExtractedPartsList = ['file2.part2.rar', 'file3.part2.rar', 'file4.part4.rar', 'file2.part3.rar']
    otherPartSkippedList = extractedPartList + nonExtractedPartsList
    clear.extract.MultipartArchiving(firstPartExtractList, otherPartSkippedList, archiveDir)
    self.assertEqual(sorted(otherPartSkippedList), sorted(nonExtractedPartsList))

  #################################################
  # Test DoRarExtraction function
  #################################################
  def test_extract_DoRarExtraction(self):
    with mock.patch('rarfile.RarFile', autospec=True) as mock_rarfile:
      rarArchive = mock_rarfile('fakepath')
      rarArchive.extract.side_effect = [Exception('Test RARfile Error'), True]

      # Check exception raised by RAR file extraction
      result = clear.extract.DoRarExtraction(rarArchive, 'target.file', 'fakedir')
      self.assertFalse(result)

      # RAR file extraction function call will do nothing and return True
      result = clear.extract.DoRarExtraction(rarArchive, 'target.file', 'fakedir')
      self.assertTrue(result)

  #################################################
  # Test GetRarPassword function
  #################################################
  @mock.patch('goodlogging.Log.Input')
  def test_extract_GetRarPassword(self, mock_input):
    skipUserInput = False

    # Check 'exit'
    mock_input.side_effect = ['exit']
    with self.assertRaises(SystemExit):
      clear.extract.GetRarPassword(skipUserInput)

    # Check 'x'
    mock_input.side_effect = ['x']
    result = clear.extract.GetRarPassword(skipUserInput)
    self.assertFalse(result)

    # Check 'rarpassword'
    mock_input.side_effect = ['rarpassword']
    result = clear.extract.GetRarPassword(skipUserInput)
    self.assertEqual(result, 'rarpassword')

    # Check empty password response
    mock_input.side_effect = ['', '', 'rarpass2']
    result = clear.extract.GetRarPassword(skipUserInput)
    self.assertEqual(result, 'rarpass2')

    # Check skipUserInput
    skipUserInput = True
    result = clear.extract.GetRarPassword(skipUserInput)
    self.assertFalse(result)

  #################################################
  # Test GetRarPassword function
  #################################################
  @mock.patch('goodlogging.Log.Input')
  def test_extract_CheckPasswordReuse(self, mock_input):
    skipUserInput = False
    mock_input.side_effect = ['t', 'a', 'n', 's']

    # Check 't' response
    result = clear.extract.CheckPasswordReuse(skipUserInput)
    self.assertEqual(result, 1)

    # Check 'a' response
    result = clear.extract.CheckPasswordReuse(skipUserInput)
    self.assertEqual(result, 2)

    # Check 'n' response
    result = clear.extract.CheckPasswordReuse(skipUserInput)
    self.assertEqual(result, 0)

    # Check 's' response
    result = clear.extract.CheckPasswordReuse(skipUserInput)
    self.assertEqual(result, -1)

    # Check invalid responses
    mock_input.side_effect = ['z', 'y', '5', 'n']
    result = clear.extract.CheckPasswordReuse(skipUserInput)
    self.assertEqual(result, 0)

    # Check skipUserInput
    skipUserInput = True
    result = clear.extract.CheckPasswordReuse(skipUserInput)
    self.assertEqual(result, 2)

  #################################################
  # Test Extract function
  #################################################
  @mock.patch('os.path.isfile')
  @mock.patch('os.rename')
  @mock.patch('clear.util.RemoveEmptyDirectoryTree')
  @mock.patch('clear.util.ArchiveProcessedFile')
  @mock.patch('clear.extract.DoRarExtraction')
  @mock.patch('clear.extract.MultipartArchiving')
  def test_extract_Extract(self, mock_multipartarchiving, mock_rarextract,
                           mock_archivefile, mock_removedirtree, mock_rename, mock_isfile):
    mock_multipartarchiving.return_value = True # Skip archiving mutlipart rar archive
    mock_rarextract.return_value = True # Skip actual RAR extraction
    mock_archivefile.return_value = True # Skip archiving extracted rar archive file
    mock_removedirtree.return_value = True # Skip directory removal
    mock_rename = True # Skip any renaming calls

    with mock.patch('rarfile.RarFile', autospec=True) as mock_rarfile:
      # Setup testcase infrastructure
      mock_rarfile_instance = mock_rarfile.return_value
      mock_rarfile_instance.needs_password.return_value = False

      filename_list = ['fileA.ff1', 'fileB.ff2', 'fileC.txt', 'fileD.log']
      s = []

      for name in filename_list:
        m = mock.MagicMock(filename=name)
        s.append(m)

      mock_rarfile_instance.infolist.return_value = s

      fileFormatList = ['.ff1', '.ff2']
      archiveDir = 'fakedir'
      skipUserInput = False

      fileList = ['filedir1/file1.rar', 'filedir2/file2.rar', 'filedir2/file3.rar']

      mock_isfile.return_value = False

      # Test rar file password options
      mock_rarfile_instance.needs_password.return_value = True

      with mock.patch('clear.extract.GetRarPassword') as mock_rarpassword:
        with mock.patch('clear.extract.CheckPasswordReuse') as mock_pwdreuse:
          mock_rarpassword.side_effect = [False, 'fakepwd1']
          mock_pwdreuse.return_value = 1
          result = clear.extract.Extract(fileList, fileFormatList, archiveDir, skipUserInput)

      # Test rar file doesn't need password
      mock_rarfile_instance.needs_password.return_value = False
      result = clear.extract.Extract(fileList, fileFormatList, archiveDir, skipUserInput)


      filename_list = ['fileA.ff1', 'fileC.txt', 'fileD.log']
      s = []

      for name in filename_list:
        m = mock.MagicMock(filename=name)
        s.append(m)

      mock_rarfile_instance.infolist.return_value = s

      fileList = ['filedir1/file1.part1.rar']

      # Test rar files extracted to sub-directory
      mock_isfile.side_effect = [False, False, True, False]
      result = clear.extract.Extract(fileList, fileFormatList, archiveDir, skipUserInput)

      # Test file already extracted at base directory
      mock_isfile.side_effect = [True, False, False]
      result = clear.extract.Extract(fileList, fileFormatList, archiveDir, skipUserInput)

      # Test file already exists at extracted sub-directory
      mock_isfile.side_effect = [False, True, False, False]
      result = clear.extract.Extract(fileList, fileFormatList, archiveDir, skipUserInput)

      # Test rar archive ImportError
      mock_rarfile.side_effect = [ImportError('Test Import Error')]
      result = clear.extract.Extract(fileList, fileFormatList, archiveDir, skipUserInput)

      # Test rar archive rarfile.NeedFirstVolume error
      mock_rarfile.side_effect = [rarfile.NeedFirstVolume]
      result = clear.extract.Extract(fileList, fileFormatList, archiveDir, skipUserInput)

      # Test rar archive other exception
      mock_rarfile.side_effect = [Exception('Test Unknown Error')]
      result = clear.extract.Extract(fileList, fileFormatList, archiveDir, skipUserInput)

      # Test empty filelist
      fileList = []
      result = clear.extract.Extract(fileList, fileFormatList, archiveDir, skipUserInput)
      self.assertIsNone(result)

if __name__ == '__main__':
  unittest.main()
