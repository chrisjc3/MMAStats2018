import requests
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import pandas as pd

pd.set_option('display.max_colwidth', -1)
pd.set_option('display.max_rows', -1)
USER_AGENT = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}

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

def getRDSsite(name, search_term):
    search_engine = "http://results.dogpile.com/serp?q=" + \
        search_term.replace(" ","+").replace(":","%3A").replace('"',"%22")
    response = requests.get(search_engine, headers=USER_AGENT)
    response.raise_for_status()
    url = ""
    soup = BeautifulSoup(response.text,"lxml")
    for div in soup.findAll("span", {"class": "url"}):
        if "fightmetric.rds" in div.contents[0] and "fighter" in div.contents[0]:
            url = str(div.contents[0])
            print(url)
            break
            
    raw_html = simple_get(url)
    with open (name + '.html', 'a') as f:
        f.write(str(raw_html))
    soup = BeautifulSoup(raw_html, 'lxml')
    return(soup)

def readPreviousHTML(name):
    with open(name + ".html", 'rb') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    print("Located data on fighter -- " + name)
    return(soup)



def getHTML(name,force):
    if force == True:
        print("Forcing hit on fighter -- " + name)
        soup = getRDSsite(name, name + ' "Saas" rds.fightmetric.com')
    else:
        try:
            soup = readPreviousHTML(name)
        except:
            print("Data not found, forcing hit on fighter -- " + name)
            soup = getRDSsite(name, name + ' "Saas" rds.fightmetric.com')
    return(soup)



def getRDSstats(name,soup):

    ###I BELIEVE THE HREF IN THE NAMES HAS OPPONENT LINK...POSSIBILITY TO COMPILE ALL OPPONENTS...
    #RDS is weird with .com .ca for fighters though...seems random

    #maybe throw together a list of opponent URLs
    
    data = pd.DataFrame()
    i = 0
    for div in soup.find("div").findAll("a", href=lambda href: href and "fighter" in href):
        data.loc[i,'Name'] = div.contents[0].replace("  ","").replace("\\n","").replace("\n","")
        i+=1
    correctRange = len(data)
    
    regex = re.compile('.*b\-table\_\_col*')
    
    i = 0
    for div in soup.findAll("td", {"class" : regex}):
        try:
            if not ":" in div.contents[0] and re.match(r'\d+', div.contents[0].replace("  ","").replace("\\n","")):
                data.loc[i,'Round'] = div.contents[0].replace("  ","").replace("\\n","")
                data.loc[i+1,'Round'] = div.contents[0].replace("  ","").replace("\\n","")
                i+=2
        except: pass
    i=0
    for div in soup.findAll("td", {"class" : regex}):
        try:
            if re.match(r'(\b[WL]\b)', div.contents[1].get_text().replace("  ","").replace("\\n","")) or \
            re.match(r'(\b(SD)\b)', div.contents[1].get_text().replace("  ","").replace("\\n","")):
                data.loc[i,'WinLoss'] = div.contents[1].get_text().replace("  ","").replace("\\n","")
                data.loc[i+1,'WinLoss'] = div.contents[1].get_text().replace("  ","").replace("\\n","")
                i+=2
        except: pass
    i=0
    for div in soup.findAll("td", {"class" : regex}):
        try:
            if re.match(r'(KO.+|.+Dec.+|Sub.+|Overt.+)', div.contents[1].get_text().replace("  ","").replace("\\n","")):
                data.loc[i,'EndMethod'] = div.contents[1].get_text().replace("  ","").replace("\\n","")
                data.loc[i+1,'EndMethod'] = div.contents[1].get_text().replace("  ","").replace("\\n","")
                i+=2
        except: pass

    divre1 = re.compile('.*fighter\_one.*')
    i = 0
    j = 0
    for div in soup.findAll("div", {"class" : divre1}):
        data.loc[i,j] = div.contents[0]
        j+=1
        if j==4:
            j=0
            i+=2

    divre2 = re.compile('.*fighter\_two.*')
    i = 1
    j = 0
    for div in soup.findAll("div", {"class" : divre2}):
        data.loc[i,j] = div.contents[0]
        j+=1
        if j==4:
            j=0
            i+=2

    data = data[0:correctRange]
    data = data.rename(index=str, columns={0: "Strike",1: "TakeDowns",2: "SubAtts",3: "GPasses"})
    return(data)






##raw_html = simple_get("http://rds.fightmetric.com/fighter/1711")
##soup = BeautifulSoup(raw_html, 'lxml')
##url = getRDSsite(name, name + ' "Saas" rds.fightmetric.com')
#soup = readPreviousHTML(name)


name = "Khabib Nurmagomedov"  #WHY THE FUCK WOULD GLEISON SHOW UP FOR KHABIB
#yea...this search engine ain't working 100% either...fucking google and their bot hate.

##name = "Jon Jones"  
##name = "Cory Sandhagen"
##name = "Michael Johnson"
soup = getHTML(name,False)

#print(soup.prettify())

data = getRDSstats(name,soup)
#woot, works on both .ca and .com
print(str(data))





