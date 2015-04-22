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
import argparse

# Local file imports
import dm
import logzila

# Variables
DATABASE_PATH = 'dm.db'

############################################################################
# ProcessArguments
############################################################################
def ProcessArguments():
  parser = argparse.ArgumentParser()
  parser.add_argument('-t', '--tags', help='enable tags on log info', action="store_true")
  parser.add_argument('--reset', help='resets database', action="store_true")
  args = parser.parse_args()

  if args.tags:
    logzila.Log.tagsEnabled = 1;

  if args.reset:
    logzila.Log.Info("MAIN", "*WARNING* YOU ARE ABOUT TO DELETE DATABASE")
    response = logzila.Log.Input("MAIN", "Are you sure you want to proceed [y/n]? ")
    if response.lower() == 'y':
      if(os.path.isfile(DATABASE_PATH)):
        os.remove(DATABASE_PATH)
    else:
      sys.exit(0)

############################################################################
# main
############################################################################
def main():
  ProcessArguments()
  prog = dm.DownloadManager(DATABASE_PATH)
  prog.ProcessDownloadFolder()

############################################################################
# default process if run as standalone
############################################################################
if __name__ == "__main__":
  if sys.version_info < (3,4):
    sys.stdout.write("[MAIN] Incompatible Python version detected - Python 3.4 or greater is required.\n")
  else:
    main()