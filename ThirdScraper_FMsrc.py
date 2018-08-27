from GoogleScraper import scrape_with_config, GoogleSearchError
import json
import os
import pandas as pd
import requests
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import numpy as np
from decimal import *
import datetime
import time
from datetime import date, datetime, time, timedelta

pd.set_option('display.max_colwidth', -1)

config = {
    'use_own_ip': True,
    'keyword': '',
    'search_engines': ['google'],
    'num_pages_for_keyword': 1,
    'scrape_method': 'http',
    'sel_browser': 'chrome',
    'do_caching': False,
    'output_filename': ''
}

##############################################################################################################################
##############################################################################################################################
##########################      URL/HTML GATHERING          ##################################################################
##############################################################################################################################
##############################################################################################################################

def readinJsonSearch(name):
    with open(name + '.json') as f:
        data = json.load(f)
    return(data)

def insertNametoConfig_Search(name, config):
    #config['keyword'] = name + ' "Saas" rds.fightmetric.com'
    config['keyword'] = name + ' site:www.fightmetric.com'
    config['output_filename'] = name + ".json"
    print("PRINTING WITH PHRASE: " + config['keyword'])
    try:
        search = scrape_with_config(config)
        data = readinJsonSearch(name)
        url_json = {}
        for res in data[0]['results']:
            if name in res['title']:
                url_json = {'name': name, 'url': str(res['link'])}
                os.remove(name + '.json')
                with open(name + '.json', 'w') as outfile:
                    json.dump(url_json, outfile)
                data = readinJsonSearch(name)
    except GoogleSearchError as e:
        print(e)
    return data

def URLFetch(name,config,force=False):
    if force == True:
        print("Forcing new search on: " + name)
        data = insertNametoConfig_Search(name,config)
    else:
        try:
            print("Checking locally for data on: " + name)
            data = readinJsonSearch(name)
            print("Found URL locally...")
        except:
            print("No URL data found, performing new search on: " + name)
            data = insertNametoConfig_Search(name,config)
    return data

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

def getRDSsite(name, url):
    raw_html = simple_get(url)
    with open (name + '.html', 'a') as f:
        f.write(str(raw_html))
    print("Stored fighter data on fighter: " + name)
    soup =readPreviousHTML(name)
    return(soup)

def readPreviousHTML(name):
    with open(name + ".html", 'rb') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    print("Importing stored data on fighter: " + name)
    return(soup)

def getHTML(name,url,force=False):
    if force == True:
        print("Forcing hit on fighter: " + name)
        soup = getRDSsite(name, url)
    else:
        try:
            soup = readPreviousHTML(name)
        except:
            print("Data not found, performing hit on fighter: " + name)
            soup = getRDSsite(name, url)
    return(soup)

##############################################################################################################################
##############################################################################################################################
#################################   SCARPER         ##########################################################################
##############################################################################################################################
##############################################################################################################################

def getRDSTablestats(name,soup):

    data = pd.DataFrame()
    i = 0
    for div in soup.findAll("a", href=lambda href: href and "fighter-details" in href): #these hrefs contain the links to opponent pages
        data.loc[i,'Name'] = div.contents[0].replace("  ","").replace("\\n","").replace("\n","").replace("\\","")
        i+=1

    correctRange = len(data)
##    print(data)

    regex = re.compile('b\-flag\_\_text')

    i=0
    for div in soup.findAll("i", {"class" : regex}):
        try:
            if re.match(r'(\b[winloss]\b)', div.contents[0][0].replace("  ","").replace("\\n","")) or \
            re.match(r'(\b(nc)\b)', div.contents[0][0:1].replace("  ","").replace("\\n","")) or \
            re.match(r'(\b(next)\b)', div.contents[0][0:3].replace("  ","").replace("\\n","")):
                data.loc[i,'WinLoss'] = div.contents[0].replace("  ","").replace("\\n","")
                data.loc[i+1,'WinLoss'] = div.contents[0].replace("  ","").replace("\\n","")
                i+=2
        except: pass
##    print(data)


    regex = re.compile('b\-fight-details\_\_table-text')
    if data['WinLoss'][0] == "next" : i = 2
    else: i = 0
    j = 0
    rowadd = 0
    for div in soup.findAll("p", {"class" : regex}):
        if re.match(r'(\d+|KO.*|DEC.*|SUB.*|.*DEC.*|Overturned|DQ|CNC)',div.contents[0].replace("  ","").replace("\\n","")):
            if j == 4 or j == 5 or j == 6 or j == 7:
                data.loc[i+rowadd,j] = div.contents[0].replace("  ","").replace("\\n","")
                data.loc[i+rowadd+1,j] = div.contents[0].replace("  ","").replace("\\n","")
                rowadd=2
            else:
                data.loc[i+rowadd,j] = div.contents[0].replace("  ","").replace("\\n","")
                rowadd+=1
            if rowadd == 2:
                rowadd = 0
                j+=1
                if j == 7:
                    j=0 
                    i+=2
##    print(data)
    data = data[0:correctRange]
    data = data.rename(index=str, columns={0: "Strike",1: "TakeDowns",2: "SubAtts",3: "GPasses",4: "EndMethod",5: "Round"})
    data = data[['Name','Strike','TakeDowns','SubAtts','GPasses','WinLoss','Round','EndMethod']]
    data[['Strike','TakeDowns','SubAtts','GPasses','Round']] = data[['Strike','TakeDowns','SubAtts','GPasses','Round']].apply(pd.to_numeric)
    
    print(data)
    return(data)

def getRDSVitalstats(name,soup):
    data = pd.DataFrame()
    i = 0
    regex = re.compile('b\-list\_\_box\-list\-item b\-list\_\_box\-list\-item\_type\_block')
    for div in soup.findAll("li", {"class" : regex}):
        try:
             if i == 0: data.loc[0, i] = div.contents[2].replace("  ","").replace("\\n","").replace("\\","") #height
             if i == 1: pass #weight
             if i == 2: data.loc[0, i] = div.contents[2].replace("  ","").replace("\\n","").replace("\\","") #reach
             if i == 3: data.loc[0, i] = div.contents[2].replace("  ","").replace("\\n","").replace("\\","") #stance
             if i == 4: pass #dob
             if i == 5: data.loc[0, i] = div.contents[2].replace("  ","").replace("\\n","").replace("\\","")#strikes landed per min
             if i == 6: data.loc[0, i] = div.contents[2].replace("  ","").replace("\\n","").replace("\\","")#strike accuracy
             if i == 7: data.loc[0, i] = div.contents[2].replace("  ","").replace("\\n","").replace("\\","")#strikes absorbed per min
             if i == 8: data.loc[0, i] = div.contents[2].replace("  ","").replace("\\n","").replace("\\","")#strike defense
             if i == 9: pass #blank
             if i == 10: data.loc[0, i] = div.contents[2].replace("  ","").replace("\\n","").replace("\\","") #TD average per 15min
             if i == 11: data.loc[0, i] = div.contents[2].replace("  ","").replace("\\n","").replace("\\","") #TD accuracy
             if i == 12: data.loc[0, i] = div.contents[2].replace("  ","").replace("\\n","").replace("\\","") #TD defense
             if i == 13: data.loc[0, i] = div.contents[2].replace("  ","").replace("\\n","").replace("\\","") #subs attempted per 15min
             i+=1
        except: pass
    
    data = data.rename(index=str, columns={0: "Height",
                                           2: "Reach",
                                           3: "Stance",
                                           5: "StrkLandpM",
                                           6: "StrkAcc",
                                           7: "StrkAbsorbpM",
                                           8: "StrkDef",
                                           10: "TDAttp15M",
                                           11: "TDAcc",
                                           12: "TDDef",
                                           13: "SubsAttp15M"})
    try:
        g = re.search(r'(\d)\'.*(\d+)\"',str(data['Height']))
        n1 = int(g.group(1))
        n2 = int(g.group(2))
        data['HeightCM'] = (n1*30.48)+(n2*2.54)
    except: data['HeightCM'] = 0 
    try:
        g = re.search(r'(\d+)\"',str(data['Reach']))
        n1 = int(g.group(1))
        data['ReachCM'] = (n1*2.54)
    except: data['ReachCM'] = 0
    print(data)

    return data


##############################################################################################################################
##############################################################################################################################
##########################################  WEIGHTS SECTION     ##############################################################
##############################################################################################################################
##############################################################################################################################

def getReachWt(vit):
    if vit['ReachCM'][0] != 0:
        factor1 = float(vit['HeightCM'])*.02
        ArmWt = ((float(vit['ReachCM']) - float(vit['HeightCM']))/factor1)*0.1
        return(round(ArmWt,3))
    else: return(0)

def getEndMethodWt(name,pf,howMany):
    pf = pf[pf.Name.str.contains(name) == True]
    pf = pf[pf.WinLoss.str.contains("next") == False]
    pf = pf[pf.WinLoss.str.contains("nc") == False]
    npf = pf[0:howMany]
    resultWt = Decimal(0)
    for i, v in npf.iterrows():
        if str(v['WinLoss']) == "win":
            try:
                g = re.search(r'(KO.*|SUB.*)',str(v['EndMethod']))
                if g.group(1) != None:
                    if int(v['Round']) == 1: resultWt= Decimal(resultWt) + Decimal(2.0)
                    if int(v['Round']) == 2: resultWt= Decimal(resultWt) + Decimal(1.5)
                    if int(v['Round']) == 3: resultWt= Decimal(resultWt) + Decimal(.5)
                    if int(v['Round']) == 4: resultWt= Decimal(resultWt) + Decimal(.2)
                    if int(v['Round']) == 5: resultWt= Decimal(resultWt) + Decimal(.1)
            except:
                resultWt= Decimal(resultWt) + Decimal(.1) 
        else:
            resultWt= Decimal(resultWt) - Decimal(.3)
    return(round(resultWt,3))

def getTendencyWts(name,pf,howMany):
    pf = pf[pf.Name.str.contains(name) == True]
    pf = pf[pf.WinLoss.str.contains("next") == False]
    npf = pf[0:howMany]

    stkWt = Decimal(sum(npf['Strike']))*Decimal(0.005)
    tdWt = Decimal(sum(npf['TakeDowns']))*Decimal(0.02)
    subWt = Decimal(sum(npf['SubAtts']))*Decimal(0.0025)
    passWt = Decimal(sum(npf['GPasses']))*Decimal(0.01)
    TendencyWt = Decimal(stkWt)+Decimal(tdWt)+Decimal(subWt)+Decimal(passWt)
    return(round(TendencyWt,3))
    
def defineWeights(name,vit,pf):
    reachWt = getReachWt(vit)
    print("Reach Wt: " + str(reachWt))
    EndMethodWt = getEndMethodWt(name, pf, 3)   #how_many previous fights to look at
    print("End Method Wt: " + str(EndMethodWt))
    TendencyWt = getTendencyWts(name, pf, 3)   #how_many previous fights to look at
    print("Tendency Wt: " + str(TendencyWt))
    Weight = Decimal(reachWt) + Decimal(EndMethodWt) + Decimal(TendencyWt)
    return(round(Weight,3))

def getFighter(name,config):
    data = URLFetch(name, config, False)
    soup = getHTML(name,data['url'], False)
##    print(soup.prettify())
    vitaldata = getRDSVitalstats(name,soup)
    tabledata = getRDSTablestats(name,soup)
    Weight = defineWeights(name,vitaldata,tabledata)
    print(str(Weight))
    return(Weight) 


########################FOR INDIVIDUAL TESTING PURPOSES######################
##name = "Jon Jones"
##name = "Artem Lobov"
##name = "Cory Sandhagen"
name = "Kalindra Faria "
Weight = getFighter(name,config)
########################FOR INDIVIDUAL TESTING PURPOSES######################


##data = pd.read_csv('DKSalaries.csv')
##data = data[['Name','ID','Salary','AvgPointsPerGame','Game Info','TeamAbbrev']]
##data = data.sort_values(by=['AvgPointsPerGame','Salary'], ascending=False)
##for i, v in data.iterrows():
##    g = re.search(r'(\w+)\@(\w+)\s.+',str(v['Game Info']))
##    nm1 = str(g.group(1))
##    nm2 = str(g.group(2))
##    if nm1 == v['TeamAbbrev']:
##        data.loc[i,'Fighter'] = nm1
##        data.loc[i,'Opponent'] = nm2
##    else:
##        data.loc[i,'Fighter'] = nm2
##        data.loc[i,'Opponent'] = nm1
##    data.loc[i,'DKID'] = str(v['Name']) + " (" + str(v['ID']) +")"
##
##for i, v in data.iterrows():
##    g = re.search(r'(.+)(\(.+)',str(v['DKID']))
##    name = str(g.group(1))
##    print(str(name))
##    Weight = getFighter(name,config)
##    data.loc[i,'Weight'] = Weight
##
##data = data[['DKID','Salary','Weight','Fighter','Opponent']]


##dt = date.today()
##dt = dt.strftime("%d%b%Y")
##writer = pd.ExcelWriter('DKReport_' + dt + '.xlsx')
##data.to_excel(writer,sheet_name='Sheet1',startrow=0, startcol=0, index=False)
##writer.save()

























