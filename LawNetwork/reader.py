import requests

with open('titles.txt') as f:
    titles = f.readlines()
    
def findTitles(billtext):
  out = []
  for t in titles:
    t = t[:-1]
    if (t in billtext):
      out.append(t)
  return out

for cn in range(117, 118):
  congress = str(cn)
  for PLnumber in range(1, 1000):
    file1 = open("map.txt", "a")  # append mode
    PLtext = str(PLnumber)
    with requests.get('https://www.congress.gov/'+congress+'/plaws/publ'+PLtext+'/PLAW-'+congress+'publ'+PLtext+'.htm') as x:
      if (x.status_code != 200):
        break
      t = findTitles(x.text)
      print(congress+'-'+PLtext, t)
      file1.write(congress+'-'+PLtext+' '+str(t)+'\n')
      file1.close()
