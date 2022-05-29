import os
import pandas as pd
import random
from bs4 import BeautifulSoup
from datetime import time
from datetime import date, datetime, timedelta
from requests_html import HTMLSession
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv, find_dotenv

sports_to_exclude = ["aussie-rules", "rugby-union", "badminton", "cycling", "horse-racing", "rugby-league",
                     "boxing", "futsal", "golf", "chess", "cricket", "trotting", "other",
                     #"volleyball", "tennis", "snooker", "basketball", "handball", "football", "ice-hockey",
                     ]


def sortByYield(row):
    return row['user_yield']


today = date.today().day
tomorrow = today + 1
now = datetime.now().time().strftime("%H:%M")
now = time(int(now[:2]), int(now[3:]), 0)

s = HTMLSession()
r = s.get("https://blogabet.com/tips/")

sleep_time = random.randint(10, 15)
print("Init after", sleep_time)
r.html.render(timeout=70, sleep=sleep_time)
soup = BeautifulSoup(r.html.raw_html, "html.parser")

all_links = soup.find_all("a", href=True)

links_to_scrap = []
bets_list = []

for link in all_links:
    href = link.get("href")
    if "blogabet.com/tips/" in href and not any(sport in link["href"] for sport in sports_to_exclude):
        print("Added link to check:", link['href'])
        links_to_scrap.append(href)
    else:
        print("Skipping link:", link['href'])
        continue


for link in links_to_scrap:
    print("Checking link: " + link)
    sleep_time = random.randint(9, 20)
    r = s.get(link)
    print("Rendering after", sleep_time)
    r.html.render(timeout=70, sleep=sleep_time)
    soup = BeautifulSoup(r.html.raw_html, "html.parser")

    bet = soup.find_all("li", class_="block media _feedPick feed-pick")

    for b in bet:
        event = b.find("div", class_="media-body").find("h3").text.strip()
        if not "Paid pick" in event:
            try:
                user_container = b.find("div", class_="feed-avatar")
                username = user_container.find("a").get("title").strip()
                user_yield = user_container.find(
                    "span", class_="u-dp data-info").text.strip().replace("\n", "").replace(" ", "")
                tips_count = user_yield[user_yield.find(
                    "(")+1:user_yield.find(")")]
                tips_effective = user_yield[:user_yield.find("%")]
                if tips_effective[0] == "-" or tips_effective[0] == "0" or tips_effective[0] == "+0" or username == "":
                    continue
                else:
                    if int(tips_effective.replace("+", "")) < 10 or int(tips_count) < 80:
                        continue

                odd = b.find("span", class_="feed-odd").text.strip()
            except:
                continue

            if "combo-pick" in link:
                combo_table = b.find("table", class_="table combo-table")
                combo_table_rows = combo_table.find_all("td")
                combo_table_rows = [row.text.strip()
                                    for row in combo_table_rows if row.text.strip() != ""]
                pick = ", ".join(combo_table_rows)
            else:
                pick = b.find(
                    "div", class_="pick-line").text.strip().replace(f"@ {odd}", "").strip()
            try:
                start = b.find("div", class_="sport-line").find("small",
                                                                class_="text-muted").text.replace("\n", "").strip().replace("Kick off:", "").replace("/                                 ", "")
            except:
                continue
            # try:
            #     content = b.find(
            #         "div", class_="feed-pick-title").find("p").text.strip()
            # except:
            #     content = ""
            if not "combo-pick" in link:
                if not "ago" in start and not "Livebet" in start:
                    if str(today) in start:
                        start_time = start.split(',')
                        start_time = start_time[1]
                        start_time = start_time.replace(
                            ' ', "").split(':')
                        bet_start_time = time(int(start_time[0])+2 if int(
                            start_time[0]) < 22 else int(start_time[0])-22, int(start_time[1]), 0)
                        if bet_start_time > now:
                            bets_list.append({"event": event, "pick": pick, "username": username, "user_yield": user_yield,
                                              "odd": odd, "start": start.replace(str(start_time[0]), str(bet_start_time)[:2]), "start_time": bet_start_time.strftime("%H:%M")})
                            print("Added Today Bet", start)
                        else:
                            continue
                    elif str(tomorrow) in start:
                        bets_list.append({"event": event, "pick": pick, "username": username, "user_yield": user_yield,
                                          "odd": odd, "start": start})
                        print("Added Tomorrow Bet", start)
                    else:
                        continue
            else:
                bets_list.append({"event": event, "pick": pick, "username": username, "user_yield": user_yield,
                                  "odd": odd, "start": start})
                print("Added Combo Bet", start)

print("Start sorting links")
bets_list = sorted(bets_list, key=sortByYield, reverse=True)
print("Start removing duplicates")
bets_list = [i for n, i in enumerate(bets_list) if i not in bets_list[n+1:]]
now = datetime.now().time().strftime("%H:%M")
now = time(int(now[:2]), int(now[3:]), 0)
print("Actual time", str(now))

bets_to_send = []
for bet in bets_list:
    if 'start_time' in bet:
        start_time = str(bet['start_time'])
        if time(int(start_time[:2]), int(start_time[3:5]), 0) > now:
            bets_to_send.append(bet)
            print("Today added", bet['start'])
        else:
            continue
    else:
        if str(tomorrow) in bet['start']:
            bets_to_send.append(bet)
            print("Tomorrow added", bet['start'])
        else:
            continue

bets_list = bets_to_send

# bets_list = [i for i in bets_list if i["start_time"]
#              > now or str(tomorrow) in i["start"]]


load_dotenv(find_dotenv())

print("Start sending emails")
smtp_server = "smtp.gmail.com"
sender_address = os.getenv("SENDER_ADDRESS")
sender_pass = os.getenv("SENDER_PASS")
receiver_address = os.getenv("RECEIVER_ADDRESS")

message = MIMEMultipart('alternative')
message['From'] = sender_address
message['To'] = receiver_address
message['Subject'] = f'Bets - Blogabet- {datetime.now().strftime("%d-%m-%Y %H:%M")}'


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

for bet in bets_list:
    message_to_send += f"<tr><td>{bet.get('username')}</td><td>{bet.get('user_yield')}</td><td>{bet.get('event')}</td><td>{bet.get('pick')}</td><td>{bet.get('odd')}</td><td>{bet.get('start')}</td></tr>"

html = html.format(message_to_send)

message.attach(MIMEText(html, 'html'))

session = smtplib.SMTP('smtp.gmail.com', 587)
session.starttls()
session.login(sender_address, sender_pass)
text = message.as_string()
session.sendmail(sender_address, receiver_address, text)
session.quit()

print("End")
