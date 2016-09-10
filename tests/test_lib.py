'''

Testbench library functions

'''
import os
import shutil
import random
import string

def GenerateRandomPath(baseName, extension=None, randomCount=10):
  randomString = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(randomCount))
  path = '{}_{}'.format(baseName, randomString)

  if extension is not None:
    path = '{}{}'.format(path, extension)

  return path

def DeleteTestPath(path):
  if os.path.isdir(path):
    shutil.rmtree(path)
  elif os.path.isfile(path):
    os.remove(path)

def GetBaseDir():
  return os.path.dirname(os.path.abspath(__file__))
