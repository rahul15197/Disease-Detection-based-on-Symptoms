import re
from googlesearch import search
import warnings
warnings.filterwarnings("ignore")
import requests
from bs4 import BeautifulSoup

# Take input a disease and return the content of wikipedia's infobox for that specific disease

def diseaseDetail(term):
    diseases=[term]
    ret=term+"\n"
    for dis in diseases:
        # search "disease wilipedia" on google 
        query = dis+' wikipedia'
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
                            symptom=str(row.find("td"))
                            symptom = symptom.replace('.','')
                            symptom = symptom.replace(';',',')
                            symptom = symptom.replace('<b>','<b> \n')
                            symptom=re.sub(r'<a.*?>','',symptom) # Remove hyperlink
                            symptom=re.sub(r'</a>','',symptom) # Remove hyperlink
                            symptom=re.sub(r'<[^<]+?>',' ',symptom) # All the tags
                            symptom=re.sub(r'\[.*\]','',symptom) # Remove citation text                     
                            symptom=symptom.replace("&gt",">")
                            ret+=data.get_text()+" - "+symptom+"\n"
#                            print(data.get_text(),"-",symptom)
                            filled = 1
                if filled:
                    break
    return ret