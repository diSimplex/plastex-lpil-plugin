
# from plasTeX.Logging import getLogger
# pluginLog = getLogger('plugin.loading')

def addConfig(config):
  print("Hello from LPiL Config PlasTeX Plugin : addConfig")

def updateConfig(config):
  print("Hello from LPiL Config PlasTeX Plugin : updateConfig")
  config['general']['renderer'] = 'Gerby'

def initPlugin(config, texStream, texDocument):
  print("Hello from LPiL Config PlasTeX Plugin : initPlugin")
