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
from timeit import default_timer as timer

def simple_get(url):
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None
    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None
    
def is_good_response(resp):
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)

def log_error(e):
    print(e)

def getNamedFighterHTML(name):
    try:
        g = re.search(r'(.+)\s(.+)',str(name))
        url = "http://www.ufc.com/fighter/" + str(g.group(1)) + "-" + str(g.group(2))
        raw_html = simple_get(url)
        with open (name + '.html', 'a') as f:
            f.write(str(raw_html))
        html = BeautifulSoup(raw_html, 'html.parser')
        return(html)
    except:
        print("Doesn't seem like they exist")

def readPreviousHTML(name):
    with open(name + ".html", 'rb') as f:
        html = BeautifulSoup(f.read(), 'html.parser')
    return(html)


def getOrHandleHTML(name, force):
    if force == True:
        try:
            print("Trying to get a hit for fighter -- Forced")
            g = re.search(r'(.+)\s(.+)',str(name))
            url = "http://www.ufc.com/fighter/" + str(g.group(1)) + "-" + str(g.group(2))
            raw_html = simple_get(url)
            with open (name + '.html', 'a') as f:
                f.write(str(raw_html))
            html = BeautifulSoup(raw_html, 'html.parser')
            return(html)
        except: print("Something went wrong with the request.")
    else:
        try:
            print("Checking locally for fighter data...")
            with open(name + ".html", 'rb') as f:
                html = BeautifulSoup(f.read(), 'html.parser')
            return(html)
        except:
            try:
                print("No data found. Trying to get a hit for fighter")
                g = re.search(r'(.+)\s(.+)',str(name))
                url = "http://www.ufc.com/fighter/" + str(g.group(1)) + "-" + str(g.group(2))
                raw_html = simple_get(url)
                with open (name + '.html', 'a') as f:
                    f.write(str(raw_html))
                html = BeautifulSoup(raw_html, 'html.parser')
                return(html)
            except: print("Something went wrong with the request.")


    
def getVITStatsfromHTML(html, name):
    data = pd.DataFrame(columns=['Name','Record','Age','Height','Weight','Arm_Reach','Leg_Reach'])
    i=0
    data.loc[i,'Name'] = name
    for p in html.select('#fighter-skill-record'):
        data.loc[i,'Record'] = p.text
    for p in html.select('#fighter-age'):
        data.loc[i,'Age'] = p.text
    for p in html.select('#fighter-height'):
        data.loc[i,'Height'] = p.text
    for p in html.select('#fighter-weight'):
        data.loc[i,'Weight'] = p.text
    for p in html.select('#fighter-reach '):
        data.loc[i,'Arm_Reach'] = p.text
    for p in html.select('#fighter-leg-reach'):
        data.loc[i,'Leg_Reach'] = p.text
    return(data)

def PrintFighterTable(name, VIT_data, PF_data):
    dt = date.today()
    dt = dt.strftime("%d%b%Y")

    writer = pd.ExcelWriter(name + '_Report_' + dt + '.xlsx')
    VIT_data.to_excel(writer,sheet_name='Sheet1',startrow=0, startcol=0, index=False)

    curlen = len(VIT_data.index)+1
    PF_data.to_excel(writer,sheet_name='Sheet1',startrow=curlen, startcol=0, index=False)

    writer.save()

def getPFStatsfromHTML(url, name):
    name_data = pd.DataFrame(columns=['names'])
    i=0
    for p in html.select('.fighter div'):
        try:
            g = re.search(r'(\w+\s\w+)',str(p.text))
            name = str(g.group(1))
            name_data.loc[i,'names'] = name
        except: name_data.loc[i,'names'] = p.text 
        i += 1
    
    num_data = pd.DataFrame(columns=['str', 'tds', 'subs', 'pass'])
    i=0
    j=0
    for p in html.select('.numeric'):
        if j == 0: num_data.loc[i,'str'] = p.text
        if j == 1: num_data.loc[i+1,'str'] = p.text
        
        if j == 2: num_data.loc[i,'tds'] = p.text
        if j == 3: num_data.loc[i+1,'tds'] = p.text

        if j == 4: num_data.loc[i,'subs'] = p.text
        if j == 5: num_data.loc[i+1,'subs'] = p.text

        if j == 6: num_data.loc[i,'pass'] = p.text
        if j == 7: num_data.loc[i+1,'pass'] = p.text
        j += 1
        if j == 8:
            j = 0
            i += 2
    
    res_data = pd.DataFrame(columns=['result'])
    i=0
    for p in html.select('.method'):
        res_data.loc[i,'result'] = p.text.replace('\n\t',' ')
        res_data.loc[i+1,'result'] = p.text.replace('\n\t',' ')
        i += 2

    wl_data = pd.DataFrame(columns=['winloss'])
    i=0
    for p in html.select('.result div'):
        wl_data.loc[i,'winloss'] = p.text
        wl_data.loc[i+1,'winloss'] = p.text
        i += 2

    frames = [name_data, num_data, res_data, wl_data]
    data = pd.concat(frames, sort=False, axis=1, ignore_index=True)
    data = data.rename(index=str, columns={0: "Name",1: "Strikes",2: "TDs",
                                           3: "SubAtts",4: "Passes",5: "Result", 6:"WinLoss"})
    data = data[data.WinLoss.str.contains("UP") == False]
    return(data)














def getArmWt(vit):
    g = re.search(r'(\d{2,})\scm',str(vit['Height']))
    heightcm = str(g.group(1))
    g = re.search(r'(\d{2,})',str(vit['Arm_Reach']))
    armcm = int(g.group(1))*2.54
    factor1 = float(heightcm)*.02
    ArmWt = ((float(armcm) - float(heightcm))/factor1)*0.1
    return(ArmWt)

def getLegWt(vit):
    g = re.search(r'(\d{2,})\scm',str(vit['Height']))
    heightcm = str(g.group(1))
    g = re.search(r'(\d{2,})',str(vit['Leg_Reach']))
    legcm = int(g.group(1))*2.54
    relativeHCM = float(heightcm)*.46
    factor1 = float(relativeHCM)*.02
    LegWt = ((float(legcm) - float(relativeHCM))/factor1)*0.01
    return(LegWt)

def getPFResultWts(name,pf,how_many):
    pf = pf[pf.Name.str.contains(name) == True]
    npf = pf[0:how_many]
    resultWt = 0
    for i, v in npf.iterrows():
        if str(v['WinLoss']) == "Win" or str(v['WinLoss']) == "":
            try:
                g = re.search(r'.+[R](\d).+(KO.+|Submiss.+)',str(v['Result']))
                rnd = int(g.group(1))
                if rnd == 1: resultWt += .5
                if rnd == 2: resultWt += .4
                if rnd == 3: resultWt += .3
                if rnd == 4: resultWt += .2
                if rnd == 5: resultWt += .1
            except: pass
            try:
                g = re.search(r'.+(Decision).+',str(v['Result']))
                if g.group(1) != None:
                    resultWt += .05
            except: pass
        else:
            resultWt += -0.2
    return(resultWt)

def getPFTendencyWts(name,pf,how_many):
    pf = pf[pf.Name.str.contains(name) == True]
    npf = pf[0:how_many]
    strkWt = 0
    tdWt = 0
    tendWt = 0
    strikes = 0
    tds = 0
    for i, v in npf.iterrows():
        strikes += int(v['Strikes'])
        tds += int(v['TDs'])
        
    strkWt = (strikes*.5)*.01
    tdWt = (tds*5)*.01
    tendWt = strkWt+tdWt
    return(tendWt)

    
def weightFighter(name, vit, pf, how_many):
    #all weights attempted to normalize around 1
    try: ArmWt = getArmWt(vit)
    except:
        print(name + " -- " + "Could not find Arm Reach Data")
        ArmWt = 0
    try: LegWt = getLegWt(vit)
    except:
        print(name + " -- " + "Could not find Leg Reach Data")
        LegWt = 0
    try: ResultWt = getPFResultWts(name,pf,how_many)
    except:
        print(name + " -- " + "Could not find Previous Result Data")
        ResultWt = 0
    try: TendencyWts = getPFTendencyWts(name,pf,how_many)
    except:
        print(name + " -- " + "Could not find Previous Result Data")
        TendencyWts = 0
    Wts = ArmWt + LegWt + ResultWt + TendencyWts
    return(Wts)



#Weights could use some work...make sure it's all adding up right too....
#Check that how_many/PF is working correctly....
#output a map with the weights onto the DF.csv as well, raw...
#look at the output against tonights' results

















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

for i, v in data.iterrows():
    g = re.search(r'(.+)(\(.+)',str(v['DKID']))
    name = str(g.group(1))
    print(str(name))
    html = getOrHandleHTML(name,False)
    VIT_data = getVITStatsfromHTML(html, name)
    PF_data = getPFStatsfromHTML(html, name)
    Weight = weightFighter(name,VIT_data,PF_data, 5)
    data.loc[i,'Weight'] = Weight

data = data[['DKID','Salary','Weight','Fighter','Opponent']]

print("Starting permutations...")


combs =  list(itertools.combinations(data['DKID'], 6))
combs = pd.DataFrame(combs)
print(str(len(combs)) + " Permutations found.") 
print("Starting Info Update & Printing...") 
finalcombs = pd.DataFrame(columns=[0,1,2,3,4,5,"Conflict","Salary","Weight"])
goodOnes = 0
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
        if len(fiList)>0 and len(opList)>0 and conflict == 0:
            for pp in fiList:
                g = re.search(r'\d+\s+(.+)',str(pp))
                f1 = str(g.group(1))
                for px in opList:
                    g = re.search(r'\d+\s+(.+)',str(px))
                    f2 = str(g.group(1))
                    if f1 == f2:
                        conflict = 1
    if(int(conflict) == 0 and float(sal)<=50000):
        finalcombs.loc[goodOnes,0] = v[0]
        finalcombs.loc[goodOnes,1] = v[1]
        finalcombs.loc[goodOnes,2] = v[2]
        finalcombs.loc[goodOnes,3] = v[3]
        finalcombs.loc[goodOnes,4] = v[4]
        finalcombs.loc[goodOnes,5] = v[5]
        finalcombs.loc[goodOnes,'Conflict'] = int(conflict)
        finalcombs.loc[goodOnes,'Salary'] = float(sal)
        finalcombs.loc[goodOnes,'Weight'] = float(wt)
        goodOnes += 1
    print("Acceptable Permutations found: " + str(goodOnes) + " -- Total records scanned: " + str(i))
print("Finished Info Update & Printing...")

dt = date.today()
dt = dt.strftime("%d%b%Y")
writer = pd.ExcelWriter('Report_' + dt + '.xlsx')
finalcombs.to_excel(writer,sheet_name='Sheet1',startrow=0, startcol=0, index=False)
writer.save()












