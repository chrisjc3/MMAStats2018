from GoogleScraper import scrape_with_config, GoogleSearchError
import json
import os

# See in the config.cfg file for possible values
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

def CheckLocalandSearch(name,config,force=False):
    if force == True:
        print("Forcing new search...")
        data = insertNametoConfig_Search(name,config)
    else:
        try:
            print("Checking locally for data...")
            data = readinJsonSearch(name)
            print("Found URL locally...")
        except:
            print("No URL data found, finding it now...")
            data = insertNametoConfig_Search(name,config)
    return data


name = "Jon Jones"
data = CheckLocalandSearch(name, config, False)

print("\n" * 10)     
print(data['url'])
