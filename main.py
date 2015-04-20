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

# Local file imports
import dm

############################################################################
# main
############################################################################
def main():
  prog = dm.DownloadManager('dm.db')
  prog.ProcessDownloadFolder()

############################################################################
# default process if run as standalone
############################################################################
if __name__ == "__main__":
  if sys.version_info < (3,4):
    sys.stdout.write("[MAIN] Incompatible Python version detected - Python 3.4 or greater is required.\n")
  else:
    main()