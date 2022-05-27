import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import date, datetime, timedelta
from requests_html import HTMLSession
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv, find_dotenv


def clean_text(text, words_to_remove, word_to_replace="", lower=True):
    if lower:
        text = text.lower().strip()
    for word in words_to_remove:
        text = text.replace(word, word_to_replace)
    return text


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


print(get_user_points("fazer77"))

read_file.to_csv('typerzy.csv', index=None, header=True)

today = date.today().day
tomorrow = today + 1

test = []

baseurl = "https://forum.bukmacherskie.com/forums/typy-dnia.43"
r = requests.get(baseurl)
soup = BeautifulSoup(r.content, 'lxml')

all_links = soup.find_all('a', href=True)
pages_to_scrap = []

for link in all_links:
    href = link.get('href')
    if f"{today}-" in href or f"{tomorrow}-" in href:
        if not 'https' in href or not 'http' in href:
            pages_to_scrap.append(href.replace("latest", ""))

pages_to_scrap = list(dict.fromkeys(pages_to_scrap))

print(pages_to_scrap)

baseurl = "https://forum.bukmacherskie.com"
for page in pages_to_scrap:
    s = HTMLSession()
    r = s.get(baseurl + page)

    r.html.render(timeout=70)
    soup = BeautifulSoup(r.html.raw_html, "html.parser")

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


load_dotenv(find_dotenv())

smtp_server = "smtp.gmail.com"
sender_address = os.getenv("SENDER_ADDRESS")
sender_pass = os.getenv("SENDER_PASS")
receiver_address = os.getenv("RECEIVER_ADDRESS")

message = MIMEMultipart('alternative')
message['From'] = sender_address
message['To'] = receiver_address
message['Subject'] = f'Bets - Forum bukmacherskie - {datetime.now().strftime("%d-%m-%Y %H:%M")}'


message_to_send = ""

html = """\
<html>
  <body>
    <table>
      <tbody>
        {}
      </tbody>
    </table>
  </body>
</html>
"""

for bet in test:
    message_to_send += f"<tr><td>{bet.get('author')}</td><td>{bet.get('points')}</td><td>{bet.get('dyscipline')}</td><td>{bet.get('start_time')}</td><td>{bet.get('match')}</td><td>{bet.get('prediction')}</td><td>{bet.get('odds')}</td><td>{bet.get('bukmacher')}</td></tr><tr><td colspan='9'>{bet.get('content')}</td></tr>"

html = html.format(message_to_send)

message.attach(MIMEText(html, 'html'))

session = smtplib.SMTP('smtp.gmail.com', 587)
session.starttls()
session.login(sender_address, sender_pass)
text = message.as_string()
session.sendmail(sender_address, receiver_address, text)
session.quit()
