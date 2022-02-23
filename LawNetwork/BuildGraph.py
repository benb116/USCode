import ast
import json
from cv2 import split
import networkx as nx

with open('short.json') as json_file:
  short = json.load(json_file)

G = nx.DiGraph()

def getPLN(refName):
  res = short[refName]
  if res[0:2] == '--':
    newref = '--'.join(res.split('--')[2:])
    return getPLN(newref)
  return res

with open('mapfull2.txt') as f:
    mapLines = f.readlines()
    mapLines.reverse()
    for line in mapLines:
      line = line[:-1]
      [pln, arrText] = line.split(' ', 1 )
      arr = ast.literal_eval(arrText)
      G.add_node(pln)
      for ref in arr:
        refpln = getPLN(ref)
        if (refpln != pln):
          # Old laws can't reference new laws
          con1 = pln.split('-')[0]
          con2 = refpln.split('-')[0]
          if len(con2) > 3:
            con2 = 1000
          if int(con2) <= int(con1):
            G.add_edge(pln, refpln)

print(list(G.edges()))
