'''

Testbench for clear.tvfile

'''
import os
import goodlogging
import unittest

import clear.tvfile

class ClearTVFile(unittest.TestCase):
  #################################################
  # Set up test infrastructure:
  #################################################
  @classmethod
  def setUpClass(cls):
    # Silence all logging messages
    goodlogging.Log.silenceAll = True

  #################################################
  # Test ShowInfo class
  #################################################
  def test_ShowInfo(self):
    invalid = clear.tvfile.ShowInfo(showID=None, showName='Invalid', seasonNum=1, episodeNum=1)
    showOne = clear.tvfile.ShowInfo(showID=1, showName='One', seasonNum=1, episodeNum=1)
    showTwo = clear.tvfile.ShowInfo(showID=2, showName='Two', seasonNum=1, episodeNum=1)
    showThreeNoneOne = clear.tvfile.ShowInfo(showID=3, showName='Three', seasonNum=None, episodeNum=1)
    showThreeOneNone = clear.tvfile.ShowInfo(showID=3, showName='Three', seasonNum=1, episodeNum=None)
    showThreeOneOne = clear.tvfile.ShowInfo(showID=3, showName='Three', seasonNum=1, episodeNum=1)
    showThreeTwoOne = clear.tvfile.ShowInfo(showID=3, showName='Three', seasonNum=2, episodeNum=1)
    showThreeTwoFive = clear.tvfile.ShowInfo(showID=3, showName='Three', seasonNum=2, episodeNum=5)

    # Sort by showname (one < two)
    result = showOne < showTwo
    self.assertIs(result, True)

    # Sort by showname (three < two)
    result = showTwo < showThreeOneOne
    self.assertIs(result, False)

    # Sort by season number
    result = showThreeOneOne < showThreeTwoOne
    self.assertIs(result, True)

    # Sort by episode number
    result = showThreeTwoOne < showThreeTwoFive
    self.assertIs(result, True)

    # Invaid showID
    result = invalid < showOne
    self.assertIs(result, False)

    # Invalid seasonNum
    result = showThreeNoneOne < showThreeTwoOne
    self.assertIs(result, False)

    # Invalid episode number
    result = showThreeOneOne < showThreeOneNone
    self.assertIs(result, False)

  #################################################
  # Test TVFile class
  #################################################
  def test_TVFile(self):
    # Test sort
    file1 = clear.tvfile.TVFile('test/file1.path')
    file2 = clear.tvfile.TVFile('test/file2.path')
    result = file1 < file2
    self.assertIs(result, False)

    # Test GetShowDetails - Invalid file path (no TV details)
    file1 = clear.tvfile.TVFile('test/file.path')
    result = file1.GetShowDetails()
    self.assertIs(result, False)

    # Test GetShowDetails - Invalid file path (duplicate TV details)
    file1 = clear.tvfile.TVFile('test/file.S01E05.S01E06.path')
    result = file1.GetShowDetails()
    self.assertIs(result, False)

    # Test GetShowDetails - Pattern: S??E??
    file1 = clear.tvfile.TVFile('test/show1.S01E05.path')
    result = file1.GetShowDetails()
    self.assertIs(result, True)
    self.assertEqual(file1.showInfo.seasonNum, '01')
    self.assertEqual(file1.showInfo.episodeNum, '05')
    self.assertEqual(file1.fileInfo.showName, 'show1')

    # Test GetShowDetails - Pattern: ?x?
    file1 = clear.tvfile.TVFile('test/show2.3x2.path')
    result = file1.GetShowDetails()
    self.assertIs(result, True)
    self.assertEqual(file1.showInfo.seasonNum, '03')
    self.assertEqual(file1.showInfo.episodeNum, '02')
    self.assertEqual(file1.fileInfo.showName, 'show2')

    # Test GetShowDetails - Pattern: S??E??E?? (multi-part episodes)
    file1 = clear.tvfile.TVFile('test/show3.S02E01E02E03.path')
    result = file1.GetShowDetails()
    self.assertIs(result, True)
    self.assertEqual(file1.showInfo.seasonNum, '02')
    self.assertEqual(file1.showInfo.episodeNum, '01')
    self.assertEqual(file1.fileInfo.showName, 'show3')
    self.assertEqual(file1.showInfo.multiPartEpisodeNumbers, ['02', '03'])

    # Test GetShowDetails - Non-consecutive multipart episode
    file1 = clear.tvfile.TVFile('test/show4.S03E05E09.path')
    result = file1.GetShowDetails()
    self.assertIs(result, True)
    self.assertEqual(file1.showInfo.seasonNum, '03')
    self.assertEqual(file1.showInfo.episodeNum, '05')
    self.assertEqual(file1.fileInfo.showName, 'show4')
    self.assertEqual(file1.showInfo.multiPartEpisodeNumbers, [])

    # Test GetShowDetails - Missing season number
    file1 = clear.tvfile.TVFile('test/show5.5E09.path')
    result = file1.GetShowDetails()
    self.assertIs(result, False)
    self.assertEqual(file1.showInfo.episodeNum, '09')
    self.assertEqual(file1.showInfo.seasonNum, None)
    self.assertEqual(file1.fileInfo.showName, None)
    self.assertEqual(file1.showInfo.multiPartEpisodeNumbers, [])

    # Test GetShowDetails - Missing show name (x pattern)
    file1 = clear.tvfile.TVFile('test/7x8.showname.path')
    result = file1.GetShowDetails()
    self.assertIs(result, False)
    self.assertEqual(file1.showInfo.episodeNum, '08')
    self.assertEqual(file1.showInfo.seasonNum, '07')
    self.assertEqual(file1.fileInfo.showName, None)
    self.assertEqual(file1.showInfo.multiPartEpisodeNumbers, [])

    # Test GetShowDetails - Missing show name (s pattern)
    file1 = clear.tvfile.TVFile('test/S7E8.path')
    result = file1.GetShowDetails()
    self.assertIs(result, False)
    self.assertEqual(file1.showInfo.episodeNum, '08')
    self.assertEqual(file1.showInfo.seasonNum, '07')
    self.assertEqual(file1.fileInfo.showName, None)
    self.assertEqual(file1.showInfo.multiPartEpisodeNumbers, [])

    # Test GenerateNewFileName - no episode name
    file1 = clear.tvfile.TVFile('test/show6.11x7.path')
    file1.GetShowDetails()
    file1.showInfo.showName = 'Show Six'
    result = file1.GenerateNewFileName()
    self.assertIsNone(result)

    # Test GenerateNewFileName - valid show info
    file1.showInfo.episodeName = 'Episode7'
    result = file1.GenerateNewFileName()
    self.assertEqual(result, 'Show Six.S11E07.Episode7.path')

    # Test GenerateNewFileName - multi-part episode
    file1 = clear.tvfile.TVFile('test/show7.S11E08E09E10.path')
    file1.GetShowDetails()
    guideShowName = 'Show Seven'
    file1.showInfo.showName = guideShowName
    file1.showInfo.episodeName = 'Episode8-10'
    result = file1.GenerateNewFileName()
    self.assertEqual(result, '{}.S11E08_09_10.Episode8-10.path'.format(guideShowName))

    # Test GenerateNewFilePath - no file dir
    file1.GenerateNewFilePath(None)
    self.assertEqual(file1.fileInfo.newPath, 'test/{}.S11E08_09_10.Episode8-10.path'.format(guideShowName))

    # Test GenerateNewFilePath - with file dir
    fileDir='/target/file/dir'
    file1.GenerateNewFilePath(fileDir)
    self.assertEqual(file1.fileInfo.newPath, os.path.join(fileDir, '{}.S11E08_09_10.Episode8-10.path'.format(guideShowName)))

    # Test Print
    file1.Print()

    # Test Print - no guide show name
    file1.showInfo.showName = None
    file1.Print()

if __name__ == '__main__':
  unittest.main()
