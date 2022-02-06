import ast
import json
import networkx as nx

with open('short.json') as json_file:
  short = json.load(json_file)

G = nx.DiGraph()

def getPLN(refName):
  res = short[refName]
  if res[0:2] == '--':
    newref = res.split('--')[-1]
    return getPLN(newref)
  return res

with open('map.txt') as f:
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
          G.add_edge(pln, refpln)

print(list(G.edges()))
