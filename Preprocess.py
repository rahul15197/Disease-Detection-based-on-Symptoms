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

stop_words = stopwords.words('english')
lemmatizer = WordNetLemmatizer()
splitter = RegexpTokenizer(r'\w+')

with open('final_dis_symp.pickle', 'rb') as handle:
    dis_symp = pickle.load(handle)
    
t0=time()
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
total_symptoms=['label_dis']+total_symptoms

print(len(diseases_symptoms_cleaned))   

t1=time()
print(t1-t0)


# Initialize two dataframes, one for normal dataset and one for combination dataset
df_comb = pd.DataFrame(columns=total_symptoms)
df_norm = pd.DataFrame(columns=total_symptoms)


# Read each disease and symptom list, convert into dictionary and add to dataframe
for key, values in diseases_symptoms_cleaned.items():
    
    key = str.encode(key).decode('utf-8')
    
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

t2=time()
print(t2-t1)


# Export disease symptoms into TXT file for better visibility
with open('dis_symp_dict.txt', 'w') as f:
  for key,value in diseases_symptoms_cleaned.items():
    print([key]+value, file=f)
