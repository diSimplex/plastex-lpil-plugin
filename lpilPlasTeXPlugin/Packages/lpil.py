#!../.venv/bin/python

# The PlasTeX version of the LPiL LaTeX style (lpil.sty)

# To complete this tool we need to:
#
# 1. *implement* the lua code called by directlua in python
#    we can do this by:
#     - writing equivalent python code,
#     - writing an argument parser (regexp)
#     - implementing a lookup table indexed by the lua function name
#     - call the looked-up python function with the supplied arguments
#     - implement the texio functions by pushing tokens back onto the
#       TeX stream.

import json
import os
import yaml

from plasTeX import subclasses, Command, Environment, VerbatimEnvironment
from plasTeX.Tokenizer import Tokenizer
from plasTeX.Logging import getLogger

log = getLogger()
status = getLogger('status')

def loadingPackage(config, texStream, texDocument, options, context) :
  context.loadLaTeXPackage(texStream, 'lpil.sty', options)

#########################################################################
# directlua implementation:
#   Initialization

def dlInitialize(tex, args) :
  pass

#########################################################################
# directlua implementation:
#   deal with dependent files and pygments options

deps = {}
pygments = {}

# directlua call implementation
def dlAddDependentFile(tex, args) :
  aFilePath = args[0]
  codeType  = 'tex'
  if 1 < len(args) and args[1] != "”" : codeType = args[1]
  print(f"\nAdding dependent file: {aFilePath} with codeType: {codeType}\n")
  deps[aFilePath] = codeType

# directlua call implementation
def dlAddPygmentsOptions(tex, args) :
  aCodeType       = args[0]
  someCodeOptions = args[1]
  pygments[aCodeType] = someCodeOptions

# directlua call implementation
def dlWriteDependentFiles(tex, args) :
  jsonDict = {
    'pygments' : pygments,
    'deps'     : deps
  }
  jsonStr = json.dumps(jsonDict)
  #print(jsonStr)

#########################################################################
# directlua implementation:
#   Input file stack

inputFiles = []

# directlua call implementation
def dlShowInputFiles(tex, args) :
  print("\nshowInputFiles:")
  print("\n-----------------------------------------")
  for aFile in inputFiles :
    print(f"{aFile} {os.path.dirname(aFile)}")
  print("-----------------------------------------")

# directlua call implementation
def dlTopInputFile(tex, args) :
  inputFile = "unknown"
  if 0 < len(inputFiles) : inputFile = inputFiles[len(inputFiles)-1]
  return inputFile

# directlua call implementation
def dlCurrentFile(tex, args) :
  return dlTopInputFile(tex, [])

# directlua call implementation
def dlCurrentDirectory(tex, args) :
  return os.path.dirname(dlTopInputFile(tex, []))

# directlua call implementation
def dlPushInputFile(tex, args) :
  aPath = args[0]
  if not (aPath.endswith('.tex') or aPath.endswith('.sty')) :
    aPath = aPath+'.tex'
  inputFiles.append(aPath)

# directlua call implementation
def dlPopInputFile(tex, args) :
  if 0 < len(inputFiles) : inputFiles.pop()

#########################################################################
# directlua implementation:
#   deal with code types

fileCounters = {}

def computeCodeTypeFileNames(tex, config, codeType, baseName) :
  # return the write, ->read<- and copy file names for this (pygmentized)
  # code
  curFilePath = dlTopInputFile(tex, [])
  curFilePathKey = curFilePath.replace('\\','.').replace('/','.')

  if codeType not in fileCounters :
    fileCounters[codeType] = {}
  codeTypeCounters = fileCounters[codeType]
  if curFilePathKey not in codeTypeCounters :
    codeTypeCounters[curFilePathKey] = {}
  curFileCounters = codeTypeCounters[curFilePathKey]
  if baseName not in curFileCounters :
    curFileCounters[baseName] = 1
  else :
    curFileCounters[baseName] = curFileCounters[baseName] + 1

  writeFileName = "".join([
    os.path.dirname(curFilePath),
    os.sep,
    baseName,
    "-",
    curFilePathKey,
    "-",
    codeType,
    f"-c{curFileCounters[baseName]:05d}",
    '.pygmented.tex'
  ])
  return os.path.join(config['lpil']['latexDir'], writeFileName)

class inputHtml(Command) :
  args = 'filePath:str'

  def invoke(self, tex) :
    a = self.parse(tex)
    filePath = a['filePath']
    try :
      with open(filePath, encoding='utf8') as htmlFile :
        self.userdata['html'] = htmlFile.read()
    except :
      log.info(f"Could not read raw html file {filePath}")
      self.userdata['html'] = f"""
<h1>Could not read raw html file: {filePath}</h1>
"""

class LpilBaseLoadCodeType(Command) :
  args = 'filePath:str'

  def invoke(self, tex) :
    a = self.parse(tex)
    filePath = a['filePath']
    pygmentedPath = computeCodeTypeFileNames(
      tex, self.config, self.codeType, filePath
    )
    inputCmd = "\\inputHtml{"+pygmentedPath+"}"
    tex.input(inputCmd)
    return []

class LpilBaseCodeType(VerbatimEnvironment) :
  args = 'baseName:str'

  def invoke(self, tex) :
    a = self.parse(tex)
    baseName = a['baseName']
    pygmentedPath = computeCodeTypeFileNames(
      tex, self.config, self.codeType, baseName
    )
    verbatim.invoke(self, tex)
    inputCmd = "\\inputHtml{"+pygmentedPath+"}"
    tex.input(inputCmd)
    return []

# dynamically creating subclasses of Command or Environment:
# see: https://www.geeksforgeeks.org/create-classes-dynamically-in-python/
# see: https://stackoverflow.com/questions/15247075/how-can-i-dynamically-create-derived-classes-from-a-base-class

# directlua call implementation
def dlNewCodeType(tex, args) :
  #"""
  #Create a new environment:
  #  - we use the latex kernel `filecontents` environment to extract the
  #    code into a file.
  #  - we expect extra latex tools to pygmentize this file
  #  - we then load in the pygmentized version
  #
  #For the PlasTeX version we probably just quietly cut out the code and
  #then load already pygmentized version directly.
  #
  #In fact we create a new VerbatimEnvironment which mimics the `comments`
  #environment in `Packages\comment.py` however WE return a raw
  #`\input{<<FILENAME>>}` for PlasTeX to parse and hence load the
  #pygmentized file.
  #"""
  codeType, pygmentOpts = args
  capCodeType = codeType[0].upper() + codeType[1:]
  name = f"loadLpil{capCodeType}Code"
  klass = type(f"{codeType}CodeTypeLoader", (LpilBaseLoadCodeType,), {
    'macroName' : name,
    'nodeName'  : name,
    'codeType'  : codeType
  })
  tex.ownerDocument.context.addGlobal(name, klass)

  name = f"lpil:{codeType}"
  klass = type(f"{codeType}CodeType", (LpilBaseCodeType,), {
    'macroName' : name,
    'nodeName'  : name,
    'codeType'  : codeType
  })
  tex.ownerDocument.context.addGlobal(name, klass)

  #print("global keys:")
  #theContext = tex.ownerDocument.context
  #for aKey in theContext.keys() :
  #  print(f"  {aKey} {repr(theContext[aKey])}")

#########################################################################
# directlua implementation:
#   deal with directlua parsing

fncDispatch = {
  'lpil.initialize'              : dlInitialize,
  'lpil.addDependentFile'        : dlAddDependentFile,
  'lpil.writeDependentFiles'     : dlWriteDependentFiles,
  'lpil.showInputFiles'          : dlShowInputFiles,
  'lpil.topInputFile'            : dlTopInputFile,
  'lpil.currentFile'             : dlCurrentFile,
  'lpil.currentDirectory'        : dlCurrentDirectory,
  'lpil.pushInputFile'           : dlPushInputFile,
  'lpil.popInputFile'            : dlPopInputFile,
  'lpil.newCodeType'             : dlNewCodeType,
  #'lpil.defineLoadPygmentedCode' : dlDefineLoadPygmentedCode
}

def aFunc(tex, someArgs) :
  aFncName = someArgs.pop(0)
  print(aFncName)
  print(yaml.dump(someArgs))

def parseCall(aCallStr) :
  if not aCallStr.startswith('lpil.') : return None
  fncName, args = aCallStr.split('(')
  args = args.rstrip(')')
  args = args.replace("’,", "',") # as mangled by Python/LaTeX?!?
  args = args.split("',")
  argStrs = []
  for anArg in args :
    strippedArg = anArg.strip(" ’'") # as mangled by Python/LaTeX?!?
    if strippedArg : argStrs.append(strippedArg)
  return (fncName, argStrs)

class directlua(Command) :
  """ \\directlua{luaCmd} """
  args = 'luaCmd'

  def invoke(self, tex) :
    a = self.parse(tex)
    luaCmd = a['luaCmd']
    print(f"\ninvoking directlua ({self.attributes['luaCmd'].source})\n")
    parsedResult = parseCall(luaCmd.source)
    if not parsedResult : return []
    fncName, args = parsedResult
    if fncName not in fncDispatch : return []
    return fncDispatch[fncName](tex, args)

#########################################################################

class newCodeType(Command) :
  """ \\newCodeType{codeType}{pygmentsOptions} """
  args = 'codeType:str pygmentsOptions:str'

  def invoke(self, tex) :
    a = self.parse(tex)
    codeType = a['codeType']
    pygmentsOpts = a['pygmentsOptions']
    return dlNewCodeType(tex, [codeType, pygmentsOpts])

class latexBuildDir(Command) :

  def invoke(self, tex) :
    tex.input(self.config['lpil']['latexDir'])

class includeLpilDiagram(Command) :
  """ \\includeLpilDiagram{lpilDiagram} """
  args = 'lpilDiagram:str'

  def invoke(self, tex) :
    a = self.parse(tex)
    lpilDiagram = a['lpilDiagram']
    curDir = dlCurrentDirectory(tex, [])
    latexDir = self.config['lpil']['latexDir']
    fullPath = os.path.join(latexDir, curDir, lpilDiagram+'.svg')
    includeGraphics = "\\includegraphics{"+fullPath+"}"
    tex.input(includeGraphics)
    return []

class lpilAddDependentFile(Command) :
  """\\lpilAddDependentFile{aPath}{aCodeType}"""
  args = "[ aCodeType:str ] aPath:str"

  def invoke(self, tex) :
    a         = self.parse(tex)
    aPath     = a['aPath']
    aCodeType = a['aCodeType']
    if not aCodeType : aCodeType = "tex"
    dlAddDependentFile(tex, [aPath, aCodeType])
    return []

class lpilPushInputFile(Command) :
  """\\lpilPushInputFile{aPath}"""
  args = "aPath:str"

  def invoke(self, tex) :
    a = self.parse(tex)
    aPath = a['aPath']
    dlPushInputFile(tex, [aPath])
    return []

class lpilPopInputFile(Command) :
  """\\lpilPopInputFile"""

  def invoke(self, tex) :
    dlPopInputFile(tex, [])
    return []

class lpilCurrentFile(Command) :
  """\\lpilCurrentFile"""

  def invoke(self, tex) :
    curFile = dlCurrentFile(tex, [])
    tex.input(curFile)
    return []

class lpilCurrentDirectory(Command) :
  """\\lpilCurrentDirectory"""

  def invoke(self, tex) :
    curDir = dlCurrentDirectory(tex, [])
    tex.input(curDir)
    return []

#########################################################################
# test test test

if __name__ == "__main__" :

  config = {
    'lpil' : {
      'latexDir' : 'build/latex'
    }
  }

  testStrs = [
    "lpil = require('lpil')",
    "lpil.initialize()",
    "lpil.addDependentFile('\\lpilCurrentDirectory#1', 'metaFun')",
    "lpil.pushInputFile('sillyDir/file1')",
    "lpil.pushInputFile('sillyDir/file2')",
    "lpil.pushInputFile('sillierDir/file3')",
    "lpil.popInputFile()",
    "lpil.currentFile()",
    "lpil.currentDirectory()",
    "lpil.showInputFiles()",
    "lpil.addDependentFile('#1')",
    "lpil.addDependentFile('#1')",
    "lpil.addDependentFile('\\latexBuildDir/\\jobname.bbl', 'cmScan')",
    "lpil.newCodeType('json', 'JsonLexer:linenos=1')",
    "lpil.newCodeType('metaFun', 'TexMetaFunLexer|linenos=1')",
    "lpil.writeDependentFiles()"
  ]

  print(yaml.dump(config))

  for aLine in testStrs :
    print("-----------------------------------------------------")
    print(aLine)
    result = parseCall(aLine)
    print(result)
    print("-----------------------------------------------------")
    if result :
      fncName, args = result
      #print(fncName)
      #print(yaml.dump(args))

      if fncName in fncDispatch :
        fncMethod = fncDispatch[fncName]
      else :
        fncMethod = aFunc
        args.insert(0, fncName)

      fncMethod(args)

  print("-----------------------------------------------------")
  print("computeCodeTypeFileNames('json', 'silly.json')")
  print(computeCodeTypeFileNames('json', 'silly.json'))
  print("-----------------------------------------------------")

  print(yaml.dump(deps))
