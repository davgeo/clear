#!/usr/bin/env python3

'''
TODO:
* TV & Movie File Renamer
* Folder organisation
* Check for new programs

This program should:
DOWNLOAD FOLDER
* Find TV shows in download folder
* Match against appropriate TV show in DB
* Rename with current episode names
* Move to TV folder

TV LIBRARY
* Check for missing episodes (new or old)
*
'''
# Python default package imports
import sys
import os
import glob

# Local file imports
import tvfile
import renamer

# Global settings
TV_TEST_DIR = 'test_dir/TV'
DL_TEST_DIR = 'test_dir/downloads'
IGNORE_DIRS = ('DONE', 'PROCESSED')
SUPPORTED_FILE_FORMATS = ('.avi','.mp4')

def GetSupportedFilesInDir(fileDir, fileList):
  print("Parsing file directory:", fileDir)
  if os.path.isdir(fileDir) is True:
    for globPath in glob.glob(os.path.join(fileDir, '*')):
      if os.path.splitext(globPath)[1] in SUPPORTED_FILE_FORMATS:
        newFile = tvfile.TVFile(globPath)
        if newFile.GetShowDetails():
          fileList.append(newFile)
      elif os.path.isdir(globPath):
        if(os.path.basename(globPath) in IGNORE_DIRS):
          print("Skipping ignored directory", globPath)
        else:
          GetSupportedFilesInDir(globPath, fileList)
      else:
        print("Ignoring unsupported file or folder:", item)
  else:
    print("Invalid non-directory path given to parse")

def ProcessDownloadFolder():
  # Get list of all video files in download directory
  # For each item
  ## Get showname, season and episode from filename
  ## Look up episode name
  ## Copy to TV directory with new name
  ## Move to PROCESSED folder in DL directory
  tvFileList = []
  GetSupportedFilesInDir(DL_TEST_DIR, tvFileList)
  tvRenamer = renamer.TVRenamer(tvFileList, 'EPGUIDES', TV_TEST_DIR)
  tvRenamer.ProcessFiles()

def main():
  ProcessDownloadFolder()

if __name__ == "__main__":
  if sys.version_info < (3,4):
    sys.stdout.write("Incompatible Python version detected - Python 3.4 or greater is required.\n")
  else:
    main()