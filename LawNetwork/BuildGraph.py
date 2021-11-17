import ast
import json
import networkx as nx
from pyvis.network import Network

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
        G.add_edge(pln, refpln)

# net = Network(notebook=True)
# net.from_nx(G)
# net.show('example.html')
indeg = list(G.in_degree())
indeg.sort(key = lambda x: x[1], reverse=True)
print(indeg)
print('done')