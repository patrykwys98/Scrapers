import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import date
from requests_html import HTMLSession


read_file = pd.read_excel('typerzy.xlsx')
read_file.to_csv('typerzy.csv', index=None, header=True)

df = pd.read_csv('typerzy.csv', delimiter=',')

today = date.today().day
tomorrow = today + 1

baseurl = "https://forum.bukmacherskie.com/forums/typy-dnia.43"
r = requests.get(baseurl)
soup = BeautifulSoup(r.content, 'lxml')

all_links = soup.find_all('a', href=True)
pages_to_scrap = []

for link in all_links:
    href = link.get('href')
    if f"{today}" in href or f"{tomorrow}" in href:
        pages_to_scrap.append(href.replace("latest", ""))


pages_to_scrap = list(dict.fromkeys(pages_to_scrap))

print(pages_to_scrap)

baseurl = "https://forum.bukmacherskie.com"
for page in pages_to_scrap:
    s = HTMLSession()
    r = s.get(baseurl + page)
    

    r.html.render(timeout=70)
    soup = BeautifulSoup(r.html.raw_html, "html.parser")

    with open('file.txt', 'w') as file:
        file.write(soup.prettify())
