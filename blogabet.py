import random
from datetime import time
from datetime import date, datetime
from get_proxies import get_proxies, get_proxies_with_proxy
from utils import scrap_with_render, send_mail, remove_duplicates
from requests_html import HTMLSession
import pandas as pd


sports_to_exclude = ["aussie-rules", "rugby-union", "badminton", "cycling", "horse-racing", "rugby-league",
                     "boxing", "golf", "chess", "cricket", "trotting", "other", 'table-tennis'
                     #"volleyball", "tennis", "snooker", "handball", "football", "ice-hockey", "baseball",
                     # "darts", "combo-pick", "e-sports",
                     #  "basketball",
                     ]


def sortByYield(row):
    return row['user_yield']


s = HTMLSession()

proxies = get_proxies(s)

today = date.today().day
tomorrow = today + 1
now = datetime.now().time().strftime("%H:%M")
now = time(int(now[:2]), int(now[3:]), 0)

soup = scrap_with_render("https://blogabet.com/tips/", session=s,
                         sleep=10, timeout=70,
                         ip=random.choice(proxies))

all_links = soup.find_all("a", href=True)
live_urls = []

links_to_scrap = []
bets_list = []

for link in all_links:
    try:
        title = link.get("title").replace(" ", "")
    except:
        title = ""
    href = link.get("href")
    if title == "Livebet":
        live_urls.append(href)
    if "blogabet.com/tips/" in href and not any(sport in link["href"] for sport in sports_to_exclude):
        print("Added link to check:", link['href'])
        links_to_scrap.append(href)
    else:
        print("Skipping link:", link['href'])
        continue

i = 0

for link in links_to_scrap:
    print("Checking link: " + link)
    i += 1
    if i > 15:
        proxy = random.choice(proxies)
        proxies = get_proxies_with_proxy(s, proxy)
        print("Getting new proxies")
        i = 0
        del proxy
    print("Changing proxy ")
    try:
        soup = scrap_with_render(
            link, session=s, sleep=random.randint(1, 5), wait=2, ip=random.choice(proxies))
        print("Rendering")
    except:
        continue

    try:
        bet = soup.find_all("li", class_="block media _feedPick feed-pick")
    except:
        print("No bets found")
        continue

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
                    if int(tips_effective.replace("+", "")) < 10 or int(tips_count) < 50:
                        continue
                    else:
                        user_link = user_container.find("a").get("href")
                        if not user_link in links_to_scrap:
                            print("append", user_link)
                            links_to_scrap.append(user_link)

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
            try:
                stake = b.find("div", class_="labels").find(
                    "span", class_="label label-default").text.strip()
            except:
                stake = "0"
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
                                              "odd": odd, "start": start.replace(str(start_time[0]), str(bet_start_time)[:2]), "start_time": bet_start_time.strftime("%H:%M"), "stake": stake})
                            print("Added Today Bet", start)
                        else:
                            continue
                    elif str(tomorrow) in start:
                        bets_list.append({"event": event, "pick": pick, "username": username, "user_yield": user_yield,
                                          "odd": odd, "start": start, "stake": stake})
                        print("Added Tomorrow Bet", start)
                    else:
                        continue
            else:
                bets_list.append({"event": event, "pick": pick, "username": username, "user_yield": user_yield,
                                  "odd": odd, "start": start, "stake": stake})
                print("Added Combo Bet", start)

print("Start sorting links")
bets_list = sorted(bets_list, key=sortByYield, reverse=True)
print("Start removing duplicates")
bets_list = remove_duplicates(bets_list)
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

df = pd.DataFrame(live_urls)
df.to_csv("live_urls.csv", index=False)

if len(bets_to_send) > 0:
    subject = f'Bets - Blogabet- {datetime.now().strftime("%d-%m-%Y %H:%M")}'
    message_to_send = ""
    for bet in bets_to_send:
        message_to_send += f"<tr><td>{bet.get('username')}</td><td>{bet.get('user_yield')}</td><td>{bet.get('event')}</td><td>{bet.get('pick')}</td><td>{bet.get('odd')}</td><td>{bet.get('stake')}</td><td>{bet.get('start')}</td></tr>"

send_mail(subject, message_to_send)
