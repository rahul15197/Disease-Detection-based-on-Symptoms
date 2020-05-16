
import pickle
import re
from googlesearch import search
import warnings
warnings.filterwarnings("ignore")
import requests
from bs4 import BeautifulSoup
import time

# Fetch disease list from 'www.nhp.gov.in'
small_alpha = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
diseases=[]
for c in small_alpha:
    URL = 'https://www.nhp.gov.in/disease-a-z/'+c
    time.sleep(1)
    page = requests.get(URL,verify=False)

    soup = BeautifulSoup(page.content, 'html5lib')
    all_diseases = soup.find('div', class_='all-disease')

    for element in all_diseases.find_all('li'):
        diseases.append(element.get_text().strip())

with open('list_diseaseNames.pkl', 'rb') as handle:
    diseases2 = pickle.load(handle)

#print(len(diseases2))
#print(len(diseases))
#print(len(set(diseases).intersection(set(diseases2))))

a=set(diseases)
b=set(diseases2)
c=list(a.union(b))
c.sort()

#print(c)

# Search diseases on google, open wikipedia page and fetch symptom from infobox

dis_symp={}
# dis1=['anthrax']
for dis in c:
  query = dis+' wikipedia'
   # search "disease wilipedia" on google 
  for sr in search(query,tld="co.in",stop=10,pause=0.5): 
       # open wikipedia link
    match=re.search(r'wikipedia',sr)
    filled = 0
    if match:
      wiki = requests.get(sr,verify=False)
      soup = BeautifulSoup(wiki.content, 'html5lib')
       # Fetch HTML code for 'infobox'
      info_table = soup.find("table", {"class":"infobox"})
      if info_table is not None:
          # Preprocess contents of infobox
        for row in info_table.find_all("tr"):
          data=row.find("th",{"scope":"row"})
          if data is not None:
            data=data.get_text()
            if data=="Symptoms":
              symptom=str(row.find("td"))
              symptom = symptom.replace('.','')
              symptom = symptom.replace(';',',')
              symptom=re.sub(r'<b.*?/b>:',',',symptom) # Remove bold text
              symptom=re.sub(r'<a.*?>','',symptom) # Remove hyperlink
              symptom=re.sub(r'</a>','',symptom) # Remove hyperlink
              symptom=re.sub(r'<[^<]+?>',', ',symptom) # All the tags
              symptom=re.sub(r'\[.*\]','',symptom) # Remove citation text
              symptom=' '.join([x for x in symptom.split() if x != ','])
              dis_symp[dis]=symptom
              # print(dis_symp[dis])
              filled = 1
              break
    if filled==1:
      break
      
#for key,value in dis_symp.items():
#  print(key,':',value)

# Remove diseases that show duplicate symptoms list
temp_list=[]
tmp_dict=dict()
for key,value in dis_symp.items():
  if value not in temp_list:
    tmp_dict[key]=value
    temp_list.append(value)
  else:
    print(key)

# Save the dictionary in PICKLE file
dis_symp = tmp_dict
print(len(dis_symp))
with open('final_dis_symp.pickle', 'wb') as handle:
   pickle.dump(dis_symp, handle, protocol=pickle.HIGHEST_PROTOCOL)
