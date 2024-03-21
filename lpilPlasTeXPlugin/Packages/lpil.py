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

import yaml

from plasTeX import Command
from plasTeX.Tokenizer import Tokenizer

def loadingPackage(config, texStream, texDocument, options, context) :
  context.loadLaTeXPackage(texStream, 'lpil.sty', options)

#def ProcessOptions(options, document) :
#  print("\nHello from lpil_plastex!\n")

class directlua(Command) :
  """ \\directlua{luaCmd} """
  args = 'luaCmd'

  def postParse(self, tex) :
    print(f"\ninvoking directlua ({self.attributes['luaCmd'].source})\n")
    #tex.pushTokens(
    #  list(Tokenizer(
    #    "\\lpilOrigInput{this_is_very_silly.tex}",
    #    tex.ownerDocument.context
    #  ))
    #)
