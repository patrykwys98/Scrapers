
import pandas as pd
import re
from datetime import date, datetime, timedelta
from get_proxies import get_proxies
import random
from utils import send_mail, clean_text, scrap_with_render
from requests_html import HTMLSession

s = HTMLSession()


def sortByPoints(row):
    return row['points']


proxies = get_proxies(s)
now = datetime.now().time().strftime("%H:%M")
now = timedelta(hours=int(now[:2]), minutes=int(now[3:]), seconds=0)


read_file = pd.read_excel('typerzy.xlsx')
read_file.drop('LP', inplace=True, axis=1)

df = read_file.to_dict('records')

def get_user_points(username):
    for i in range(len(df)):
        if df[i].get('U2ytkownik') == str(username):
            return df[i].get('Punkty')
    return 0


read_file.to_csv('typerzy.csv', index=None, header=True)

today = date.today().day
tomorrow = today + 1

test = []

baseurl = "https://forum.bukmacherskie.com/forums/typy-dnia.43"
soup = scrap_with_render(baseurl, session=s, timeout=20, sleep=5,
                         ip=random.choice(proxies))

all_links = soup.find_all('a', href=True)
pages_to_scrap = []

for link in all_links:
    href = link.get('href')
    if f"{today}-" in href or f"{tomorrow}-" in href:
        if not 'https' in href or not 'http' in href:
            pages_to_scrap.append(href.replace("latest", ""))

pages_to_scrap = list(dict.fromkeys(pages_to_scrap))


baseurl = "https://forum.bukmacherskie.com"
for page in pages_to_scrap:
    soup = scrap_with_render(baseurl + page, session=s, timeout=20,
                             sleep=5, ip=random.choice(proxies))

    bets = soup.find_all('div', class_="message-inner")

    for bet in bets:

        text = bet.find('div', class_="bbWrapper").text.replace(
            "\n\n\n\n\n\n\n\n\n\n", "\n").replace(
                "\n\n\n\n\n\n\n", "\n").replace(
                    "\n\n\n\n\nwww.sofascore.com\n\n\n\n\n", "").replace(
                        "\n\n\n\n\nwww.oddsportal.com\n\n\n\n\n\n", "").strip()
        author = bet.find('a', class_="username").text if bet.find(
            'a', class_="username").text else bet.find('span', class_=re.compile("^username-")).text
        splited_text = text.split("\n")
        dyscipline = splited_text[0]
        start_time = clean_text(
            splited_text[1], ["godzina:", "godzina :" "godzina", "cet", "może ulec", "godzina"]).replace(" ", "").replace(".", ":")
        match = splited_text[2]
        prediction = splited_text[3]
        odds = splited_text[4]
        bukmacher = splited_text[5]
        content = " ".join(splited_text[6:])

        if start_time == "":
            start_time = "00:00"
        elif not ":" in start_time:
            start_time = start_time + ":00"

        bet_to_append = {
            "author": author,
            "points": get_user_points(author),
            "dyscipline": clean_text(dyscipline, []),
            "start_time": start_time,
            "match": match,
            "prediction": prediction,
            "odds": odds,
            "bukmacher": bukmacher,
            "content": content,
        }

        start_time = bet_to_append['start_time'].split(':')
        if not "Tutaj podajemy typy" in text:
            if str(today) in str(page):
                try:
                    bet_start_time = timedelta(hours=int(start_time[0]), minutes=int(
                        start_time[1]), seconds=0)
                except:
                    bet_start_time = timedelta(hours=0, minutes=0, seconds=0)
                if (bet_start_time - now).total_seconds() > 0:
                    test.append(bet_to_append)
            elif str(tomorrow) in str(page):
                test.append(bet_to_append)
            else:
                print("Old bet")

test.sort(key=sortByPoints, reverse=True)

subject = f'Bets - Forum bukmacherskie - {datetime.now().strftime("%d-%m-%Y %H:%M")}'
message_to_send = ""
for bet in test:
    message_to_send += f"<tr><td>{bet.get('author')}</td><td>{bet.get('points')}</td><td>{bet.get('dyscipline')}</td><td>{bet.get('start_time')}</td><td>{bet.get('match')}</td><td>{bet.get('prediction')}</td><td>{bet.get('odds')}</td><td>{bet.get('bukmacher')}</td></tr><tr><td colspan='9'>{bet.get('content')}</td></tr>"
send_mail(subject, message_to_send)
