import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from requests_html import HTMLSession
import re
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv, find_dotenv

today = date.today().day
tomorrow = today + 1

now = datetime.now().time().strftime("%H:%M")
now = timedelta(hours=int(now[:2]), minutes=int(now[3:]), seconds=0)
bets_list = []


def sortByEffective(bet):
    return bet['effective']


def scrap_zawod_typer():
    baseurl = "https://zawodtyper.pl/"

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
        found_pages_to_scrap += 1
        s = HTMLSession()
        r = s.get(page)
        try:
            r.html.render(sleep=30, timeout=210)
        except:
            print("Error while rendering")
            continue
        soup = BeautifulSoup(r.html.raw_html, "html.parser")

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


tries = 0

scrap_zawod_typer()

if len(bets_list) == 0:
    while tries < 5:
        if len(bets_list) > 0:
            break
        tries += 1
        scrap_zawod_typer()

bets_list.sort(key=sortByEffective, reverse=True)

load_dotenv(find_dotenv())

if len(bets_list) > 0:
    smtp_server = "smtp.gmail.com"
    sender_address = os.getenv("SENDER_ADDRESS")
    sender_pass = os.getenv("SENDER_PASS")
    receiver_address = os.getenv("RECEIVER_ADDRESS")

    message = MIMEMultipart('alternative')
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = f'Bets - Zawód Typer - {datetime.now().strftime("%d-%m-%Y %H:%M")}'

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
    bets_message = ""
    for bet in bets_list:
        bets_message += f"<tr><td>{bet.get('effective')}</td><td>{bet.get('author')}</td><td>{bet.get('dyscipline')}</td><td>{bet.get('prediction')}</td><td>{bet.get('match')}</td><td>{bet.get('start')}</td><td>{bet.get('odds')}</td><td>{bet.get('bukmacher')}</td></tr></tr><tr><td colspan='9'>{bet.get('content')}</td></tr>"

    html = html.format(bets_message)

    message.attach(MIMEText(html, 'html'))

    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls()
    session.login(sender_address, sender_pass)
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
