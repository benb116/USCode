import requests

with open('titles.txt') as f:
    titles = f.readlines()
    # Some titles are substrings of other titles
    # E.g. OBRA and COBRA (two different acts)
    # Naive substring search would catch cobra when searching for obra
    # Sort titles by length (descending)
    # And remove them after they've been found
    stitles = sorted(titles, key=len)
    stitles.reverse()
    
def findTitles(billtext):
  # Text cleanup
  billtext = billtext.replace('\n','')
  billtext = ' '.join(billtext.split())

  out = []
  for t in stitles:
    t = t[:-1]
    if (t in billtext):
      out.append(t)
      # Remove all instances so substrings are not found
      billtext = billtext.replace(t, '')
  
  return out

for cn in range(104, 118):
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
