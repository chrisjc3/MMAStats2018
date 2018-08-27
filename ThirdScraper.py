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

pd.set_option('display.max_colwidth', -1)
##pd.set_option('display.max_rows', -1)

config = {
    'use_own_ip': True,
    'keyword': ' "Saas" rds.fightmetric.com',
    'search_engines': ['google'],
    'num_pages_for_keyword': 1,
    'scrape_method': 'http',
    'sel_browser': 'chrome',
    'do_caching': False,
    'output_filename': ''
}

def readinJsonSearch(name):
    with open(name + '.json') as f:
        data = json.load(f)
    return(data)

def insertNametoConfig_Search(name, config):
    config['keyword'] = name + config['keyword']
    config['output_filename'] = name + ".json"
    #print("PRINTING WITH PHRASE: " + config['keyword'])
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
    soup = BeautifulSoup(raw_html, 'lxml')
    return(soup)

def readPreviousHTML(name):
    with open(name + ".html", 'rb') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    print("Located data on fighter: " + name)
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

def getRDSVitalstats(name,soup):
    data = pd.DataFrame()
    i = 0
    regex = re.compile('b\-box\_\_value')
    for div in soup.findAll("i", {"class" : regex}):
        try:
             if i == 0: pass
             if i == 1: data.loc[0, i] = div.contents[0].replace("  ","").replace("\\n","").replace("\\","")
             if i == 2: data.loc[0, i] = div.contents[0].replace("  ","").replace("\\n","").replace("\\","")
             if i == 3: data.loc[0, i] = int(div.contents[0].replace("  ","").replace("\\n","").replace("\\",""))
             if i == 4: data.loc[0, i] = div.contents[0].replace("  ","").replace("\\n","").replace("\\","")
             if i >= 5: pass
             i+=1
        except: pass
    data = data.rename(index=str, columns={1: "Height",2: "Reach",3: "Age",4: "Stance"})

    g = re.search(r'(\d)\'.*(\d+)\"',str(data['Height']))
    n1 = int(g.group(1))
    n2 = int(g.group(2))
    data['HeightCM'] = (n1*30.48)+(n2*2.54)

    g = re.search(r'(\d+)\"',str(data['Reach']))
    n1 = int(g.group(1))
    data['ReachCM'] = (n1*2.54)
    data = data[['Height','HeightCM','Reach','ReachCM','Age','Stance']]
    
    return data

def getRDSTablestats(name,soup):

    ###I BELIEVE THE HREF IN THE NAMES HAS OPPONENT LINK...POSSIBILITY TO COMPILE ALL OPPONENTS...

    data = pd.DataFrame()
    i = 0
    
    for div in soup.find("div").findAll("a", href=lambda href: href and "fighter" in href):
        data.loc[i,'Name'] = div.contents[0].replace("  ","").replace("\\n","").replace("\n","").replace("\\","")
        i+=1

    correctRange = len(data)
##    print(data)
    regex = re.compile('.*b\-table\_\_col*')

    i=0
    for div in soup.findAll("td", {"class" : regex}):
        try:
            if re.match(r'(\b[WL]\b)', div.contents[1].get_text().replace("  ","").replace("\\n","")) or \
            re.match(r'(\b(SD)\b)', div.contents[1].get_text().replace("  ","").replace("\\n","")) or \
            re.match(r'(\b(NEXT)\b)', div.contents[1].get_text().replace("  ","").replace("\\n","")):
                data.loc[i,'WinLoss'] = div.contents[1].get_text().replace("  ","").replace("\\n","")
                data.loc[i+1,'WinLoss'] = div.contents[1].get_text().replace("  ","").replace("\\n","")
                i+=2
        except: pass
##    print(data)
    
    if data['WinLoss'][0] == "NEXT" : i = 2
    else: i = 0
    for div in soup.findAll("td", {"class" : regex}):
        try:
            if not ":" in div.contents[0] and re.match(r'(\d+)', div.contents[0].replace("  ","").replace("\\n","")):
                data.loc[i,'Round'] = int(div.contents[0].replace("  ","").replace("\\n",""))
                data.loc[i+1,'Round'] = int(div.contents[0].replace("  ","").replace("\\n",""))
                i+=2
        except: pass
##    print(data)
    
    if data['WinLoss'][0] == "NEXT" : i = 2
    else: i = 0
    for div in soup.findAll("td", {"class" : regex}):
        try:
            if re.match(r'(KO.+|.+Dec.+|Sub.+|Overt.+|DQ)', div.contents[1].get_text().replace("  ","").replace("\\n","")):
                data.loc[i,'EndMethod'] = div.contents[1].get_text().replace("  ","").replace("\\n","")
                data.loc[i+1,'EndMethod'] = div.contents[1].get_text().replace("  ","").replace("\\n","")
                i+=2
        except: pass
##    print(data)
    
    divre1 = re.compile('.*fighter\_one.*')
    if data['WinLoss'][0] == "NEXT" : i = 2
    else: i = 0
    j = 0
    for div in soup.findAll("div", {"class" : divre1}):
        try:
            data.loc[i,j] = int(div.contents[0])
            j+=1
            if j==4:
                j=0
                i+=2
        except: pass
##    print(data)

    divre2 = re.compile('.*fighter\_two.*')
    if data['WinLoss'][0] == "NEXT" : i = 3
    else: i = 1
    j = 0
    for div in soup.findAll("div", {"class" : divre2}):
        try:
            data.loc[i,j] = int(div.contents[0])
            j+=1
            if j==4:
                j=0
                i+=2
        except: pass
##    print(data)

    data = data[0:correctRange]
    data = data.rename(index=str, columns={0: "Strike",1: "TakeDowns",2: "SubAtts",3: "GPasses"})
    data = data[['Name','Strike','TakeDowns','SubAtts','GPasses','WinLoss','Round','EndMethod']]
    
    return(data)


def getReachWt(data):
    factor1 = float(data['HeightCM'])*.02
    ArmWt = ((float(data['ReachCM']) - float(data['HeightCM']))/factor1)*0.1
    return(ArmWt)




def defineWeights(vit,pf):
    reachWt = getReachWt(vit)
    print(str(reachWt))
    return



##name = "Jon Jones"
name = "Artem Lobov"
data = URLFetch(name, config, False)
soup = getHTML(name,data['url'], False)

##print(soup.prettify())

tabledata = getRDSTablestats(name,soup)
vitaldata = getRDSVitalstats(name,soup)


data = defineWeights(vitaldata,tabledata)


##vitals_factor
##prevfights_factor



writer = pd.ExcelWriter(name + '_Report.xlsx')
vitaldata.to_excel(writer,sheet_name=name,startrow=0, startcol=0, index=False)
tabledata.to_excel(writer,sheet_name=name,startrow=3, startcol=0, index=False)
writer.save()

























