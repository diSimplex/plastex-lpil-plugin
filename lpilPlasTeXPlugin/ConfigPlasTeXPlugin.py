
import os
import tomllib

from plasTeX.ConfigManager import *

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
      os.getenv("HOME"), ".config", "cfdoit", "config.toml"
    )
  )

def updateConfig(config):
  #print("Hello from LPiL Config PlasTeX Plugin : updateConfig")

  config['general']['renderer'] = 'LPiLGerby'

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

def initPlugin(config, texStream, texDocument):
  print("Hello from LPiL Config PlasTeX Plugin : initPlugin")
