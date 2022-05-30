import re
from get_proxies import get_proxies
import random
from datetime import timedelta, datetime

from utils import scrap_with_render, get_dates, send_mail


bets_list = []

proxies = get_proxies()

today, tomorrow, now = get_dates()


def sortByEffective(bet):
    return bet['effective']

baseurl = "https://zawodtyper.pl/"

pages = []
soup = scrap_with_render(url=baseurl, sleep=20,
                            timeout=20, ip=random.choice(proxies))

links = soup.find(
    'section', class_='typy-dnia-glowna only-desktop pt-12 pb-16 bg-prime').find_all('a')

for link in links:

    href = link.get('href')
    if str(href)[0] != '/':
        if str(today) in href or str(tomorrow) in href:
            pages.append(href)

pages = list(dict.fromkeys(pages))

for page in pages:
    soup = scrap_with_render(
        url=page, sleep=2, timeout=70, ip=random.choice(proxies))
    bets = soup.find_all(
        'div', id=re.compile("^typ-"), class_="relative")
    for bet in bets:
        fields = bet.find_all("fieldset")
        try:
            effective = bet.find(
                'div', class_="absolute top-0 right-[30px] bg-body-lighter shadow shadow-prime-darker rounded-b-md p-1 lg:right-[58px] overflow-hidden after:only-mobile after:absolute after:bg-white after:w-[10%] after:h-full after:top-0 after:right-[150px] after:animate-[like-shine_24s_ease-in-out_infinite] after:blur after:skew-x-12 after:transition-transform").find('p', class_="text-[12px] px-1 text-center font-bold lg:text-[14px]").text
        except:
            effective = ""
        try:
            dyscipline = fields[0].div.text,
        except:
            dyscipline = ""
        try:
            match = fields[1].div.text
        except:
            match = ""
        try:
            prediction = fields[2].div.text
        except:
            prediction = ""
        try:
            odds = fields[3].div.text
        except:
            odds = ""
        try:
            start = fields[4].div.text
        except:
            start = ""
        try:
            bukmacher = fields[5].div.text
        except:
            bukmacher = ""
        try:
            content = bet.find('div', id=re.compile("^content")).text
        except:
            content = ""
        try:
            author = bet.find(
                'a', class_="block w-[calc(100%_-_75px)] max-w-fit text-ellipsis whitespace-nowrap overflow-hidden !no-underline leading-[1.2] !text-text hover:!text-text-darker").span.text
        except:
            author = ""
        formatted_bet = {
            'effective': effective,
            'dyscipline':  dyscipline,
            'match': match,
            'prediction': prediction,
            'odds': odds,
            'start': start,
            'bukmacher': bukmacher,
            'content': content,
            'author': author,
        }
        start_time = formatted_bet['start'].split(':')
        if str(today) in str(page):
            bet_start_time = timedelta(hours=int(start_time[0]), minutes=int(
                start_time[1]), seconds=0)
            if (bet_start_time - now).total_seconds() > 0:
                bets_list.append(formatted_bet)
bets_list.sort(key=sortByEffective, reverse=True)

if len(bets_list) > 0:
    subject = f'Bets - Zawód typer - {datetime.now().strftime("%d-%m-%Y %H:%M")}'
    bets_message = ""
    for bet in bets_list:
        bets_message += f"<tr><td>{bet.get('effective')}</td><td>{bet.get('author')}</td><td>{bet.get('dyscipline')}</td><td>{bet.get('prediction')}</td><td>{bet.get('match')}</td><td>{bet.get('start')}</td><td>{bet.get('odds')}</td><td>{bet.get('bukmacher')}</td></tr></tr><tr><td colspan='9'>{bet.get('content')}</td></tr>"
    send_mail(subject, bets_message)

