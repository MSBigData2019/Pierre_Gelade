# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 18:14:21 2018

@author: Pro
"""

# coding: utf-8
import requests,re
from bs4 import BeautifulSoup
import pandas as pd

def importSoup(NomEnt):
    url = r"https://www.reuters.com/finance/stocks/financial-highlights/" + NomEnt
    res = requests.get(url)
    if res.status_code == 200:
        html_doc =  res.text
        soup = BeautifulSoup(html_doc,"html.parser")
    return soup


def rechercheChamps(soup,dicValeurs):

    text_Targeted = "Quarter Ending Dec-18"
    dicValeurs[text_Targeted] = soup.find_all("tr",attrs={'class':'stripe'})[0].contents[5].text
    
    text_Targeted = "Prix Action"      
    dicValeurs[text_Targeted] = soup.find_all('span', attrs={'style':'font-size: 23px;'})[0].string.strip()
    
    text_Targeted = "valueContentPercent"
    dicValeurs[text_Targeted] = soup.find_all("span",attrs={'class':text_Targeted})[0].text.strip()[1:-1]

    text_Targeted = "% Shares Owned:"
    dicValeurs[text_Targeted] = soup.find("td",text = text_Targeted).findNext("td").text
                
    text_Targeted = "Dividend Yield"
    dicValeurs[text_Targeted + " company"] = soup.find("td",text = text_Targeted).findNext("td").text
    dicValeurs[text_Targeted + " industry"] = soup.find("td",text = text_Targeted).findNext("td").findNext("td").text
    dicValeurs[text_Targeted + " sector"] = soup.find("td",text = text_Targeted).findNext("td").findNext("td").findNext("td").text
    
    return dicValeurs


def rechercheUrl(query):
    url = "https://www.reuters.com/finance/stocks/lookup?search=" + query + "&searchType=any&sortBy=&dateRange=&comSortBy=marketcap"
    res = requests.get(url)
    if res.status_code == 200:
        html_doc =  res.text
        soup = BeautifulSoup(html_doc,"html.parser")
        lurl = soup.find_all("tr",attrs={'class':'stripe'})
        for ur in lurl:
            if re.search(".PA",ur.contents[3].text):
                return ur.contents[3].text

dico={}

listEnt = ("airbus","LVMH","Danone")

for query in listEnt:
    del dicValeurs
    dicValeurs = {}
    NomEnt = rechercheUrl(query)
    soup = importSoup(NomEnt)
    rechercheChamps(soup,dicValeurs)
    dico[query]=dicValeurs
    
print(dico)


