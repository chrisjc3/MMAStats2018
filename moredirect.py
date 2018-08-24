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



    
def weightFighter(name, vit, pf):
####ALL weights maximum = 1 to keep them relative   

    ArmWt = getArmWt(vit)
    LegWt = getLegWt(vit)




    return








name1 = "James Vick"
#html = getNamedFighterHTML(name1) #<---saves to html now
html = readPreviousHTML(name1)  #<---can load html from previous runs...reduces hits,
                                #produces same data (slight exception for RESULT, can regex)

VIT_data = getVITStatsfromHTML(html, name1)
PF_data = getPFStatsfromHTML(html, name1)
##PrintFighterTable(name1, VIT_data, PF_data)










data = weightFighter(name1,VIT_data,PF_data)

#print(str(data))


#takedowns x .1
#sweeps x .1
#passes x .1


#average last 3 of previous fight stats
    #->would love to rank the oppenents for a weight...would = lot of hits unless I started keeping a repo

#average pts of result



##Significant Strikes
##+0.5 Pts
##
##Advance
##+3 Pts
##
##Takedown
##+5 Pts
##
##Reversal/Sweep
##+5 Pts
##
##Knockdown
##+10 Pts

##1st Round Win
##+90 Pts
##2nd Round Win
##+70 Pts
##3rd Round Win
##+45 Pts
##4th Round Win
##+40 Pts
##5th Round Win
##+40 Pts
##Decision Win
##+30 Pts



##    OV_data = OV_data[['TotalStrikes','SuccStrikes','SuccStrikePerc','StrikingDefensePerc',
##    'TotalTDAttempts','SuccTDs','SuccTDPerc','TDDefensePerc',
##    'Submissions','Sweeps','Passes',
##    'ClinchStrikesLanded','ClinchStrikePerc','GroundStrikesLanded','GroundStrikePerc','StandingStrikesLanded','StandingStrikePerc'
##    ]]
##

#PF Data = Strikes TDs SubAtts Passes Result




#maybe weight it out...define some kind of 'score'...would like to base off level of competition but that would need a lot of hits
#then compare the scores of opponent...obviously...
#eventually import draftkings salaries & put in some kind of differential 





#http://www.ufc.com/fighter/Tyron-Woodley
#http://www.ufc.com/fighter/Justin-Gaethje


###how to iterate it....
##for v in data.iterrows():
##    print(str(v[1][0]) + " --- " + str(v[1][1]) + "\n")
