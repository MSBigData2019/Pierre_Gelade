# -*- coding: utf-8 -*-
"""
Éditeur de Spyder

Ceci est un script temporaire.
"""

# coding: utf-8
import requests,re
from bs4 import BeautifulSoup
import pandas as pd

def importSoup(url):
    request_headers = {
       "Accept-Language": "en-US,en;q=0.5",
       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
       "Referer": "http://thewebsite.com",
       "Connection": "keep-alive"
    }
    res = requests.get(url, headers = request_headers)
    if res.status_code == 200:
        html_doc =  res.text
        soup = BeautifulSoup(html_doc,"html.parser")
        return soup
    
def Extract_All_Zoe(url):
    soup = importSoup(url)
    specific_class = "clearfix trackable"
    all_links = map(lambda x : x.attrs['href'] , soup.find_all("a", class_= specific_class))
    return all_links  

def Extract_Caracts_Zoe(all_links,df):
    i = 1
    dico = {}
    for link in all_links:
        urlCar = 'https://www.leboncoin.fr' + link
        soupCar = importSoup(urlCar)
        dico['NomCar'] = [x.text for x in soupCar.findAll("h1", {"class" : "_1KQme"})][0]

        regVers = re.compile(('zen|intens|life'))
        Vers = regVers.search(dico['NomCar'].lower())
        dico['Version'] = [Vers.group(0) if Vers else 'NC']
        
        Caracts = [x.text for x in soupCar.findAll("div", {"class" : "_3Jxf3"})]

        dico['Annee'] = int(Caracts[2])

        dico['Km']  = int(str.replace(Caracts[3],' km',''))
        
        pri = [x.text for x in soupCar.findAll("span", {"class" : "_1F5u3"})][0]
        dico['Prix']  = int(str.replace(''.join(pri.split(' ')),'€',''))

        dfTemp = pd.DataFrame(dico,index=[i])

        df = pd.concat([df,dfTemp])
        i += 1
    return df

def RechercheLienCoteArgus(Version,Annee):
    urlArgus = 'https://www.lacentrale.fr/cote-voitures-renault-zoe--{}-.html'.format(Annee)
    soupArgus = importSoup(urlArgus)
    all_linksArg = map(lambda x : x.attrs['href'] , soupArgus.find_all("a"))
    
    for link in all_linksArg:
        if re.search('cote-auto-renault-zoe',link) and re.search(Version,link):
            linkArgus = 'https://www.lacentrale.fr/' + link
            break
        else :
            linkArgus = 'NonTrouvee'
    return linkArgus


def RecherchePrixArgus(linkArgus):
    if linkArgus == 'NonTrouvee':
        return linkArgus
    else:
        soupArgusCar = importSoup(linkArgus)
        priArgus = [x.text for x in soupArgusCar.findAll("span", {"class" : "jsRefinedQuot"})][0]
        return int(''.join(priArgus.split(' ')))

def TraitementZoe(dfZoes):
    for index, row in dfZoes.iterrows():
        if row['Version'] == 'NC':
            dfZoes.at[index, 'PrixArgus'] = 0
        else:
            linkArgus = RechercheLienCoteArgus(row['Version'], row['Annee'])
            dfZoes.at[index, 'PrixArgus'] = RecherchePrixArgus(linkArgus)
    return dfZoes[dfZoes['PrixArgus'] > dfZoes['Prix']]

##### MAIN #############
url = r"https://www.leboncoin.fr/recherche/?category=2&text=renault%20zoe&regions=12"
all_links_Zoe = Extract_All_Zoe(url)

dfZoes = pd.DataFrame()

dfZoes = Extract_Caracts_Zoe(all_links_Zoe,dfZoes)

dfZoesFavorable =  TraitementZoe(dfZoes)

print(dfZoesFavorable[['NomCar','Prix','PrixArgus']])























