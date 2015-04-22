''' LOGGING '''
# Python default package imports

# Custom Python package imports

# Local file imports

#################################################
# Log
#################################################
class Log:
  tagsEnabled = 0
  maxTagSize = 8
  indent = 0
  indentSize = '  '
  verbosity = 100

  ############################################################################
  # IncreaseIndent
  ############################################################################
  def IncreaseIndent():
    Log.indent = Log.indent + 1

  ############################################################################
  # ResetIndent
  ############################################################################
  def ResetIndent():
    Log.indent = 0

  ############################################################################
  # DecreaseIndent
  ############################################################################
  def DecreaseIndent():
    Log.indent = Log.indent - 1
    if Log.indent < 0:
      Log.indent = 0

  ############################################################################
  # CreateString
  ############################################################################
  def CreateString(tag, string):
    returnString = ""
    if Log.tagsEnabled:
      tag = tag[0:Log.maxTagSize].upper()
      returnString = "[{0}]{1}".format(tag, ' '*(Log.maxTagSize-len(tag)))
    returnString = returnString + "{0}{1}".format(Log.indent*Log.indentSize, string)
    return returnString

  ############################################################################
  # Info
  ############################################################################
  def Info(tag, string):
    print(Log.CreateString(tag, string))

  ############################################################################
  # Input
  ############################################################################
  def Input(tag, string):
    response = input(Log.CreateString(tag, string))
    return response

  ############################################################################
  # Seperator
  ############################################################################
  def Seperator():
    print("\n*** -------------------------------- ***")

  ############################################################################
  # NewLine
  ############################################################################
  def NewLine():
    print("")
