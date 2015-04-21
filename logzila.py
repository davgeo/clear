''' LOGGING '''
# Python default package imports

# Custom Python package imports

# Local file imports

#################################################
# Log
#################################################
class Log:
  tagsEnabled = 1
  maxTagSize = 8
  indent = 0
  indentSize = '  '
  verbosity = 100

  def IncreaseIndent():
    Log.indent = Log.indent + 1

  def DecreaseIndent():
    Log.indent = Log.indent - 1
    if Log.indent < 0:
      Log.indent = 0

  def CreateString(tag, string):
    returnString = ""
    if Log.tagsEnabled:
      tag = tag[0:Log.maxTagSize].upper()
      returnString = "[{0}]{1}".format(tag, ' '*(Log.maxTagSize-len(tag)))
    returnString = returnString + "{0}{1}".format(Log.indent*Log.indentSize, string)
    return returnString

  def Info(tag, string):
    print(Log.CreateString(tag, string))

  def Input(tag, string):
    response = input(Log.CreateString(tag, string))
    return response

  def Seperator():
    print("\n*** -------------------------------- ***")

############################################################################
# main
############################################################################
def main():
  print(Log.indent)
  print(Log.verbosity)
  Log.Info("Main", "Test")
  Log.IncreaseIndent()
  Log.Info("Main", "Test")
  Log.Input("Main", "Enter: ")

############################################################################
# default process if run as standalone
############################################################################
if __name__ == "__main__":
  main()