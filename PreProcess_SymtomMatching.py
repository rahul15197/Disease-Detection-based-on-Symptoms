import csv
import pickle
import re
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from itertools import combinations
from time import time
from nltk.tokenize import RegexpTokenizer
from collections import OrderedDict
import warnings
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.naive_bayes import MultinomialNB
from statistics import mean
from nltk.corpus import wordnet 
import requests
from bs4 import BeautifulSoup
from collections import Counter
import operator
from xgboost import XGBClassifier
import math

# returns the list of synonyms of the input word from thesauras.com and wordnet
def synonyms(term):
    synonyms = []
    response = requests.get('https://www.thesaurus.com/browse/{}'.format(term))
    soup = BeautifulSoup(response.content,  "html.parser")
    try:
        container=soup.find('section', {'class': 'MainContentContainer'}) 
        row=container.find('div',{'class':'css-191l5o0-ClassicContentCard'})
        row = row.find_all('li')
        for x in row:
            synonyms.append(x.get_text())
    except:
        None
    for syn in wordnet.synsets(term):
        synonyms+=syn.lemma_names()
    return set(synonyms) 

stop_words = stopwords.words('english')
lemmatizer = WordNetLemmatizer()
splitter = RegexpTokenizer(r'\w+')

with open('final_dis_symp.pickle', 'rb') as handle:
    dis_symp = pickle.load(handle)
    
total_symptoms = set() # Stores all unique symptoms
diseases_symptoms_cleaned = OrderedDict() # Key: disease, Value:[List of symptoms]

# Iterate over all disease and preprocess symptoms string and break it into individual symptom
for key in sorted(dis_symp.keys()):
    value = dis_symp[key]
    list_sym = re.sub(r"\[\S+\]", "", value).lower().split(',')
    temp_sym = list_sym
    list_sym = []
    for sym in temp_sym:
        if len(sym.strip())>0:
            list_sym.append(sym.strip())
    # Remove 'none' from symptom
    if "none" in list_sym: 
        list_sym.remove("none");
    if len(list_sym)==0:
        continue
    temp = list()
    for sym in list_sym:
        sym=sym.replace('-',' ')
        sym=sym.replace("'",'')
        sym=sym.replace('(','')
        sym=sym.replace(')','')
        sym = ' '.join([lemmatizer.lemmatize(word) for word in splitter.tokenize(sym) if word not in stop_words and not word[0].isdigit()])
        total_symptoms.add(sym)
        temp.append(sym)
    diseases_symptoms_cleaned[key] = temp
    
total_symptoms = list(total_symptoms)
total_symptoms.sort()
print(len(total_symptoms))

# stores each symptom's synonyms as a list of words
sym_syn = dict()
for s in total_symptoms:
    symp=s.split()
    str_sym=set()
    for comb in range(1, len(symp)+1):
        for subset in combinations(symp, comb):
            subset=' '.join(subset)
            subset = synonyms(subset) 
            str_sym.update(subset)
    str_sym.add(s)
    str_sym = ' '.join(str_sym).replace('_',' ').lower()
    str_sym = list(set(str_sym.split()))
    str_sym.sort()
    sym_syn[s] = str_sym
#    print(s,":",str_sym)
print("Done!")

# For each symptom pair in dataset, find Jaccard score of their synonym list.
# If Jaccard>threshold, it means that those sysnonyms are similar and one of them can be 
# used in place of other
total_symptoms = sorted(total_symptoms, key=len, reverse=True) 
symptom_match=dict()
new_symptoms = set()
for i,symi in enumerate(total_symptoms):
    for j in range(i+1,len(total_symptoms)):
        symj=total_symptoms[j]
        syn_symi = set(sym_syn[symi])
        syn_symj = set(sym_syn[symj])
        jaccard = len(syn_symi.intersection(syn_symj))/len(syn_symi.union(syn_symj))
        if jaccard>0.75:
            print(symi,"->",symj)
            # Store similar symptoms in dictionary, replace symj with symi, so  
            # symptom_match[symj] = symi
            if symi in symptom_match.keys():
                symptom_match[symj] =  symptom_match[symi]
            else:
                symptom_match[symj] = symi
new_symptoms = set(total_symptoms).difference(set(symptom_match.keys()))
print(len(new_symptoms))

#print(symptom_match)

# After removing similar symptoms, final list of symptoms is stores in new_symptoms
total_symptoms = new_symptoms
total_symptoms = list(total_symptoms)
total_symptoms.sort()
total_symptoms=['label_dis']+total_symptoms

# Initialize two dataframes, one for normal dataset and one for combination dataset
df_comb = pd.DataFrame(columns=total_symptoms)
df_norm = pd.DataFrame(columns=total_symptoms)

# Read each disease and symptom list, convert into dictionary and add to dataframe
for key, values in diseases_symptoms_cleaned.items():
    key = str.encode(key).decode('utf-8')
    tmp = []
    
    # For similar symptoms, replace with the value in dictionary
    for symptom in values:
        if symptom in symptom_match.keys():
            tmp.append(symptom_match[symptom])
            # print(symptom)
        else:
            tmp.append(symptom)
            
    values = list(set(tmp))
    diseases_symptoms_cleaned[key] = values
    
    # Populate row for normal
    row_norm = dict({x:0 for x in total_symptoms})
    for sym in values:
        row_norm[sym] = 1
    row_norm['label_dis']=key
    df_norm = df_norm.append(pd.Series(row_norm), ignore_index=True)
         
    # Populate rows for combination dataset
    for comb in range(1, len(values) + 1):
        for subset in combinations(values, comb):
            row_comb = dict({x:0 for x in total_symptoms})
            for sym in list(subset):
                row_comb[sym]=1
            row_comb['label_dis']=key
            df_comb = df_comb.append(pd.Series(row_comb), ignore_index=True)

print(df_comb.shape)
print(df_norm.shape)
     
# Export the dataset into CSV files      
df_comb.to_csv("dis_sym_dataset_comb.csv",index=None)
df_norm.to_csv("dis_sym_dataset_norm.csv",index=None)

# Export disease symptoms into TXT file for better visibility
with open('dis_symp_dict.txt', 'w') as f:
  for key,value in diseases_symptoms_cleaned.items():
    print([key]+value, file=f)

