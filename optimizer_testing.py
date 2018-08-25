from __future__ import division, unicode_literals 
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import pandas as pd
from tkinter import *
from tkinter.ttk import *
from tkinter import ttk, messagebox, filedialog
import datetime
import time
from datetime import date, datetime, time, timedelta
import xlsxwriter
import codecs
import itertools




####Get DK data in and ready
data = pd.read_csv('DKSalaries.csv')
data = data[['Name','ID','Salary','AvgPointsPerGame','Game Info','TeamAbbrev']]
data = data.sort_values(by=['AvgPointsPerGame','Salary'], ascending=False)


for i, v in data.iterrows():
    g = re.search(r'(\w+)\@(\w+)\s.+',str(v['Game Info']))
    nm1 = str(g.group(1))
    nm2 = str(g.group(2))
    if nm1 == v['TeamAbbrev']:
        data.loc[i,'Fighter'] = nm1
        data.loc[i,'Opponent'] = nm2
    else:
        data.loc[i,'Fighter'] = nm2
        data.loc[i,'Opponent'] = nm1
    data.loc[i,'DKID'] = str(v['Name']) + " (" + str(v['ID']) +")"
    
data = data[['DKID','Salary','AvgPointsPerGame','Fighter','Opponent']]
data = data.rename(index=str, columns={"AvgPointsPerGame": "Weight"})

combs =  list(itertools.combinations(data['DKID'], 6))
combs = pd.DataFrame(combs)

for i, v in combs.iterrows():
    opList = []
    fiList = []
    sal = 0
    wt = 0
    conflict = 0
    for j in v:
        line = data[data.DKID == str(j)]
        sal += float(line.Salary)
        wt += float(line.Weight)
        opList.append(str(line.Opponent))
        fiList.append(str(line.Fighter))
        if len(fiList)>0 and len(opList)>0:
            #if any(s in str(fiList) for s in str(opList)):
            if not set(fiList).isdisjoint(opList):
                conflict = 1
    combs.loc[i,'Conflict'] = str(conflict)
    combs.loc[i,'Salary'] = str(sal)
    combs.loc[i,'Weight'] = str(wt)
    print(str(combs.iloc[i]))


writer = pd.ExcelWriter('Report' + '.xlsx')
combs.to_excel(writer,sheet_name='Sheet1',startrow=0, startcol=0, index=False)
writer.save()


















