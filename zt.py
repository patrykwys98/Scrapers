import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date, datetime, timedelta
from requests_html import HTMLSession
import re
import os

today = date.today().day
tomorrow = today + 1

now = datetime.now().time().strftime("%H:%M")
now = timedelta(hours=int(now[:2]), minutes=int(now[3:]), seconds=0)

baseurl = "https://zawodtyper.pl/"

value_bets_list = []
less_value_bets_list = []
recent_bets_list = []

pages = []

r = requests.get(baseurl)
soup = BeautifulSoup(r.content, 'lxml')

links = soup.find(
    'section', class_='typy-dnia-glowna only-desktop pt-12 pb-16 bg-prime').find_all('a')

found_pages_to_scrap = 0

for link in links:

    href = link.get('href')
    if str(href)[0] != '/':
        if str(today) in href or str(tomorrow) in href:
            pages.append(href)


pages = list(dict.fromkeys(pages))

for page in pages:
    print(page)
    found_pages_to_scrap += 1
    s = HTMLSession()
    r = s.get(page)

    r.html.render(wait=4)
    soup = BeautifulSoup(r.html.raw_html, "html.parser")

    bets = soup.find_all(
        'div', id=re.compile("^typ-"), class_="relative")

    for bet in bets:
        try:
            fields = bet.find_all("fieldset")
            formatted_bet = {
                'effective': bet.find(
                    'div', class_="absolute top-0 right-[30px] bg-body-lighter shadow shadow-prime-darker rounded-b-md p-1 lg:right-[58px]").find('p', class_="text-[12px] px-1 text-center font-bold lg:text-[14px]").text,
                'dyscipline':  fields[0].div.text,
                'match': fields[1].div.text,
                'prediction': fields[2].div.text,
                'odds': fields[3].div.text,
                'start': fields[4].div.text,
                'bukmacher': fields[5].div.text,
                'content': bet.find('div', id=re.compile("^content")).text,
                'author': bet.find('a', class_="block w-[calc(100%_-_75px)] max-w-fit text-ellipsis whitespace-nowrap overflow-hidden !no-underline leading-[1.2] !text-text hover:!text-text-darker").span.text

            }
            if str(today) in str(page):
                bet_start_time = timedelta(hours=int(formatted_bet['start'][:2]), minutes=int(
                    formatted_bet['start'][3:]), seconds=0)

                if (bet_start_time - now).total_seconds() > 0:
                    if int(formatted_bet.get('effective')[0]) > 6:
                        value_bets_list.append(formatted_bet)
                        print("Value bet added")
                    else:
                        less_value_bets_list.append(formatted_bet)
                        print("Less value bet added")
                else:
                    recent_bets_list.append(formatted_bet)
            else:
                if int(formatted_bet.get('effective')[0]) > 6:
                    value_bets_list.append(formatted_bet)
                    print("Value bet added")
                else:
                    less_value_bets_list.append(formatted_bet)
                    print("Less value bet added")
        except:
            print("Something went wrong")

if not os.path.exists('zt'):
    os.mkdir('zt')


if len(value_bets_list) > 0:
    df = pd.DataFrame(value_bets_list)
    df.to_csv(f'zt/{today}-zawodtyper_value_bets.csv', index=False)


if len(less_value_bets_list) > 0:
    df = pd.DataFrame(less_value_bets_list)
    df.to_csv(f'zt/{today}-zawodtyper_less_value_bets.csv', index=False)

if len(recent_bets_list) > 0:
    df = pd.DataFrame(recent_bets_list)
    df.to_csv(f'zt/{today}-zawodtyper_recent_bets.csv', index=False)

print(f"Scraped {str(found_pages_to_scrap)} pages")
