import ast
import json
import networkx as nx

with open('short.json') as json_file:
  short = json.load(json_file)
with open('dates.json') as dates_json_file:
  dates = json.load(dates_json_file)

G = nx.DiGraph()

def getPLN(refName):
  if refName[0:6] == 'Act of':
    res = dates[refName[7:]]
  else:
    res = short[refName]

  if res[0:2] == '--':
    newref = '--'.join(res.split('--')[2:])
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
          # Old laws can't reference new laws
          con1 = pln.split('-')[0].split(':')[0]
          con2 = refpln.split('-')[0].split(':')[0]
          a = len(con1)
          b = len(con2)
          if a > 4 or b > 4:
            continue
          
          i = int(con1)
          j = int(con2)

          if a < 4 and b < 4:
            if j <= i:
              G.add_edge(pln, refpln)
          elif a < 4 and b >= 4:
            if i * 2 + 1787 > j:
              G.add_edge(pln, refpln)
          elif a >= 4 and b < 4:
            if j * 2 + 1787 < i:
              G.add_edge(pln, refpln)
          else:
            if j <= i:
              G.add_edge(pln, refpln)

print(list(G.edges()))
