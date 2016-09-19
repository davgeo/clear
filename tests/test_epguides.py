'''

Testbench for clear.epguides

'''
import os
import datetime
import goodlogging
import unittest
import unittest.mock as mock

import clear.epguides

class ClearEpguides(unittest.TestCase):
  #################################################
  # Set up test infrastructure
  #################################################
  @classmethod
  def setUpClass(cls):
    # Silence all logging messages
    goodlogging.Log.silenceAll = True

  #################################################
  # Mock csv format
  #################################################
  def mock_csv_format(self, list_to_csv):
    mock_csv_str = ''
    for row in list_to_csv:
      if mock_csv_str != '':
        mock_csv_str += '\n'
      mock_csv_str += ','.join(row)
    return mock_csv_str

  #################################################
  # Test _ParseShowList function
  #################################################
  def test_epguies_ParseShowList(self):
    guide = clear.epguides.EPGuidesLookup()

    # Test valid csv file format
    mock_allshow_list = (('title', guide.ID_LOOKUP_TAG), ('testshow1','1'), ('testshow2','2'))
    guide._allShowList = self.mock_csv_format(mock_allshow_list)

    guide._ParseShowList(True) # Test checkOnly=True
    self.assertIsNone(guide._showTitleList)
    self.assertIsNone(guide._showIDList)

    guide._ParseShowList()

    expectedTitleList = [i[0] for c, i in enumerate(mock_allshow_list) if c > 0]
    expectedIDList = [i[1] for c, i in enumerate(mock_allshow_list) if c > 0]

    self.assertEqual(guide._showTitleList, expectedTitleList)
    self.assertEqual(guide._showIDList, expectedIDList)

    # Test invalid csv file format - invalid title
    mock_allshow_list = (('invalidtitle', guide.ID_LOOKUP_TAG), ('testshow1','1'), ('testshow2','2'))
    guide._allShowList = self.mock_csv_format(mock_allshow_list)

    with self.assertRaises(SystemExit):
      guide._ParseShowList()

    # Test invalid csv file format - invalid tag name
    mock_allshow_list = (('title', 'invalidtagname'), ('testshow1','1'), ('testshow2','2'))
    guide._allShowList = self.mock_csv_format(mock_allshow_list)

    with self.assertRaises(SystemExit):
      guide._ParseShowList()

  #################################################
  # Test _GetAllShowList function
  #################################################
  @mock.patch('os.path.exists')
  def test_epguies_GetAllShowList(self, mock_pathexists):
    guide = clear.epguides.EPGuidesLookup()

    # Test load from file
    mock_pathexists.return_value = True

    mock_allshow_list = (('title', guide.ID_LOOKUP_TAG), ('testshow1','1'), ('testshow2','2'))
    mock_allshow_str = self.mock_csv_format(mock_allshow_list)

    with mock.patch('clear.epguides.open', mock.mock_open(read_data=mock_allshow_str), create=True) as mock_open:
      guide._GetAllShowList()
    self.assertEqual(guide._allShowList, mock_allshow_str)

    # Test web lookup
    mock_pathexists.return_value = False

    mock_allshow_list = (('title', guide.ID_LOOKUP_TAG), ('testshow3','3'), ('testshow4','4'))
    mock_allshow_str = self.mock_csv_format(mock_allshow_list)

    with mock.patch('clear.util.WebLookup') as mock_weblookup:
      mock_weblookup.return_value = mock_allshow_str

      with mock.patch('clear.epguides.EPGuidesLookup._ParseShowList') as mock_parseshowlist:
        # Test with invalid showlist format detected
        mock_parseshowlist.return_value = False
        guide._GetAllShowList()
        self.assertEqual(guide._allShowList, mock_allshow_str)

        # Test with valid showlist format detected
        with mock.patch('clear.epguides.open', mock.mock_open(), create=True) as mock_open:
          # Test all show csv file write
          expectedSaveFilePath = os.path.join(guide._saveDir, '_epguides_' + datetime.date.today().strftime("%Y%m%d") + '.csv')
          mock_parseshowlist.return_value = True
          guide._GetAllShowList()
          mock_open.assert_called_once_with(expectedSaveFilePath, 'w')
          mock_open_handle = mock_open()
          mock_open_handle.write.assert_called_once_with(guide._allShowList)

          # Test old file removal
          with mock.patch('glob.glob') as mock_glob:
            with mock.patch('os.remove') as mock_remove:
              expectedGlobPath = os.path.join(guide._saveDir, '_epguides_????????.csv')
              expectedDeleteFilePath = os.path.join(guide._saveDir, '_epguides_' + (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d") + '.csv')
              mock_glob.return_value = [expectedSaveFilePath, expectedDeleteFilePath]
              guide._GetAllShowList()
              mock_glob.assert_called_once_with(expectedGlobPath)
              mock_remove.assert_called_once_with(expectedDeleteFilePath)

  #################################################
  # Test _GetTitleAndIDList function
  #################################################
  @mock.patch('clear.epguides.EPGuidesLookup._GetAllShowList')
  @mock.patch('clear.epguides.EPGuidesLookup._ParseShowList')
  def test_epguies_GetTitleAndIDList(self, mock_parseshowlist, mock_getallshow):
    guide = clear.epguides.EPGuidesLookup()

    # Test with empty allShowList
    guide._GetTitleAndIDList()
    self.assertIs(mock_getallshow.called, True)
    self.assertIs(mock_parseshowlist.called, True)

    # Test with non-empty allShowList
    mock_getallshow.reset_mock()
    mock_parseshowlist.reset_mock()
    guide._allShowList = 'not empty'
    guide._GetTitleAndIDList()
    self.assertIs(mock_getallshow.called, False)
    self.assertIs(mock_parseshowlist.called, True)

  #################################################
  # Test _GetTitleList function
  #################################################
  @mock.patch('clear.epguides.EPGuidesLookup._GetTitleAndIDList')
  def test_epguies_GetTitleList(self, mock_gettitleandidlist):
    guide = clear.epguides.EPGuidesLookup()

    # Test with empty allShowList
    guide._GetTitleList()
    self.assertIs(mock_gettitleandidlist.called, True)

    # Test with non-empty allShowList
    mock_gettitleandidlist.reset_mock()
    guide._showTitleList = 'not empty'
    guide._GetTitleList()
    self.assertIs(mock_gettitleandidlist.called, False)

  #################################################
  # Test _GetIDList function
  #################################################
  @mock.patch('clear.epguides.EPGuidesLookup._GetTitleAndIDList')
  def test_epguies_GetIDList(self, mock_gettitleandidlist):
    guide = clear.epguides.EPGuidesLookup()

    # Test with empty allShowList
    guide._GetIDList()
    self.assertIs(mock_gettitleandidlist.called, True)

    # Test with non-empty allShowList
    mock_gettitleandidlist.reset_mock()
    guide._showIDList = 'not empty'
    guide._GetIDList()
    self.assertIs(mock_gettitleandidlist.called, False)

  #################################################
  # Test _GetShowID function
  #################################################
  @mock.patch('clear.epguides.EPGuidesLookup._GetTitleList')
  @mock.patch('clear.epguides.EPGuidesLookup._GetIDList')
  def test_epguies_GetShowID(self, mock_getidlist, mockgettitlelist):
    guide = clear.epguides.EPGuidesLookup()

    # Test with invalid title list
    guide._showTitleList = []
    result = guide._GetShowID('TestShowName')
    self.assertIsNone(result)

    # Test with valid title list
    guide._showTitleList = ['TestShowName1', 'TestShowName2', 'TestShowName3']
    guide._showIDList = ['3','86','2']

    for index, show in enumerate(guide._showTitleList):
      result = guide._GetShowID(show)
      self.assertEqual(result, guide._showIDList[index])

  #################################################
  # Test _ExtractDataFromShowHtml function
  #################################################
  def test_epguies_ExtractDataFromShowHtml(self):
    guide = clear.epguides.EPGuidesLookup()

    # Test correct data extraction
    data = 'HTML DATA HERE'
    html = """OTHER
            <pre>
              {}
            </pre>
            STUFF
            <div>HERE</div>""".format(data)
    result = guide._ExtractDataFromShowHtml(html)
    self.assertEqual(result, data)

    # Test invalid data extraction
    html = 'OTHER<broken>{}</broken>STUFF<div>HERE</div>'.format(data)
    with self.assertRaises(Exception):
      result = guide._ExtractDataFromShowHtml(html)

  #################################################
  # Test _GetEpisodeName function
  #################################################
  def test_epguies_GetEpisodeName(self):
    guide = clear.epguides.EPGuidesLookup()

    # Test valid episode name lookup
    showID = '20'
    season = '2'
    episode = '5'
    expectedTitle = '2x5 Episode Title'
    showInfoList = [['season', 'episode', 'title'],
                    ['2','4','2x4 Episode Title'],
                    [season, episode, expectedTitle],
                    ['2','corrupted6','2x6 Episode Title']]
    guide._showInfoDict[showID] = '\n'.join([','.join(i) for i in showInfoList])
    result = guide._GetEpisodeName(showID, season, episode)
    self.assertEqual(result, expectedTitle)

    # Test invalid episode name lookup
    season = 3
    result = guide._GetEpisodeName(showID, season, episode)
    self.assertIsNone(result)

  #################################################
  # Test ShowNameLookUp function
  #################################################
  @mock.patch('clear.epguides.EPGuidesLookup._GetTitleList')
  def test_epguiesShowNameLookUp(self, mock_gettitlelist):
    guide = clear.epguides.EPGuidesLookup()
    guide._showTitleList = ['TestShow1', 'TestShow2', 'TestShow3', 'TestShow25']

    # Match all
    result = guide.ShowNameLookUp('Test')
    self.assertEqual(result, guide._showTitleList)

    # Match 1
    result = guide.ShowNameLookUp('Show1')
    self.assertEqual(result, ['TestShow1'])

    # Match 2 and 25
    result = guide.ShowNameLookUp('Show2')
    self.assertEqual(result, ['TestShow2', 'TestShow25'])

    # Exact match 2
    result = guide.ShowNameLookUp('TestShow2')
    self.assertEqual(result, ['TestShow2'])

  #################################################
  # Test EpisodeNameLookUp function
  #################################################
  @mock.patch('clear.util.WebLookup')
  @mock.patch('clear.epguides.EPGuidesLookup._GetShowID')
  def test_epguiesEpisodeNameLookUp(self, mock_getshowid, mock_weblookup):
    guide = clear.epguides.EPGuidesLookup()

    showName = 'Test ShowName'
    showID = '10'
    season = '7'
    episode = '2'
    expectedTitle = '7x2 Episode Title'
    showInfoList = [['season', 'episode', 'title'],
                    ['3','4','3x4 Episode Title'],
                    [season, episode, expectedTitle],
                    ['8','corrupted6','8x6 Episode Title']]
    showInfoDictData = '\n'.join([','.join(i) for i in showInfoList])

    html = """<pre>
              {}
              </pre>""".format(showInfoDictData)

    mock_weblookup.return_value = html
    mock_getshowid.return_value = showID

    # Test without a previously populated show dictionary
    result = guide.EpisodeNameLookUp(showName, season, episode)
    mock_getshowid.assert_called_once_with(showName)
    mock_weblookup.assert_called_once_with(guide.EPISODE_LOOKUP_URL, {guide.EP_LOOKUP_TAG: showID})
    self.assertEqual(result, expectedTitle)

    # Test with a (now) populated show dictionary
    season = '3'
    episode = '4'
    expectedTitle = '3x4 Episode Title'
    result = guide.EpisodeNameLookUp(showName, season, episode)
    self.assertEqual(mock_getshowid.call_count, 2)
    self.assertEqual(mock_weblookup.call_count, 1)
    self.assertEqual(result, expectedTitle)

    # Test with a invalid show id
    mock_getshowid.return_value = None
    result = guide.EpisodeNameLookUp(showName, season, episode)
    self.assertIsNone(result)

if __name__ == '__main__':
  unittest.main()
