
import os
import tomllib

from plasTeX.ConfigManager import *
from plasTeX.Tokenizer import Tokenizer

# from plasTeX.Logging import getLogger
# pluginLog = getLogger('plugin.loading')

def addConfig(config):
  #print("Hello from LPiL Config PlasTeX Plugin : addConfig")

  section = config.addSection("lpil", "LPiL renderer options")

  section["latexDir"] = StringOption(
    """Location of LaTeX build directory""",
    options = "--latex-dir",
    default = os.path.join("build", "latex")
  )

  section["lpilConfig"] = StringOption(
    """Location of LPiL configuration file""",
    options = "--lpil-config",
    default = os.path.join(
      os.getenv("HOME"), ".config", "lpil", "config.toml"
    )
  )

  section["docTag"] = StringOption(
    """The unique Gerby tag of this document""",
    options = "--lpil-doc-tag",
    default = ""
  )

  section['collection'] = StringOption(
    """The LPiL collection to use to compute chapter numbers""",
    options = "--lpil-collection",
    default = ""
  )

def updateConfig(config, fileName):
  #print("Hello from LPiL Config PlasTeX Plugin : updateConfig")

  config['general']['renderer'] = 'LPiLGerby'

  if 'gerby' not in config['logging']['logging'] :
    config['logging']['logging']['gerby'] = 40

  configFile = config['lpil']['lpilConfig']
  if configFile :
    lpilConfig = { 'build': {}}
    try :
      with open(config['lpil']['lpilConfig'], 'rb') as cf :
        lpilConfig = tomllib.load(cf)
    except FileNotFoundError :
      print("Could not load LPiL configuration from: ")
      print(f"  {configFile}")
      print("using defaults...")

    if 'latexDir' in lpilConfig['build'] :
      latexDir = lpilConfig['build']['latexDir']
      if 'buildDir' in lpilConfig['build'] :
        latexDir = latexDir.replace(
          '$buildDir', lpilConfig['build']['buildDir']
        )
      config['lpil']['latexDir'] = latexDir

    lpilDocTag = os.path.splitext(os.path.basename(fileName))[0]
    if not config['lpil']['docTag'] :
      config['lpil']['docTag'] = lpilDocTag

    if not config['images']['base-url'] :
      config['images']['base-url'] = '/docs/'+lpilDocTag

def getTokenizerOn(fileName, texStream) :
  try:
    encoding = texStream.ownerDocument.config['files'].get('input-encoding', 'utf_8_sig')
  except (KeyError, AttributeError):
    encoding = 'utf_8_sig'

  if encoding in ['utf8', 'utf-8', 'utf_8']:
    encoding = 'utf_8_sig'

  fname = texStream.kpsewhich(fileName)
  openFile = open(fname, encoding=encoding)
  return Tokenizer(openFile, texStream.ownerDocument.context)


def initPlugin(config, fileName, texStream, texDocument):
  #print("Hello from LPiL Config PlasTeX Plugin : initPlugin")

  # We implement our LPiL Magic comments
  # see: https://tex.stackexchange.com/questions/78101/when-and-why-should-i-use-tex-ts-program-and-tex-encoding
  #
  # NOTE: All magic comments MUST be BEFORE the first blank line!
  #       AND must have a '%' as the FIRST character on the line!

  if texStream.toplevel and os.path.isfile(fileName) :
    with open(fileName) as baseFile :
      for aLine in baseFile :
        if not aLine.startswith('%') : break
        if '!LPiL' not in aLine : continue
        if '=' in aLine :
          if 'preamble' in aLine :
            preAmble = aLine.split('=')[1].strip()
            if os.path.isfile(preAmble) :
              #print(f"Found preamble {preAmble}")
              t = getTokenizerOn(preAmble, texStream)
              texStream.inputs.append((t, iter(t)))
              texStream.currentInput = texStream.inputs[-1]
          elif 'postamble' in aLine :
            postAmble = aLine.split('=')[1].strip()
            if os.path.isfile(postAmble) :
              #print(f"Found postamble {postAmble}")
              t = getTokenizerOn(postAmble, texStream)
              texStream.inputs.insert(0, (t, iter(t)))
              texStream.currentInput = texStream.inputs[-1]
          elif 'collection' in aLine :
            collection = aLine.split('=')[1].strip()
            config['lpil']['collection'] = collection
