from requests_html import HTMLSession
from bs4 import BeautifulSoup
import random


def get_proxies():
    url = "https://free-proxy-list.net/"
    session = HTMLSession()
    r = session.get(url)
    r.html.render(timeout=70)
    soup = BeautifulSoup(r.html.raw_html, "html.parser")

    table = soup.find("table", class_="table table-striped table-bordered")
    proxies = []
    for row in table.find_all("tr"):
        columns = row.find_all("td")
        if(columns != []):
            ip = columns[0].text.strip()
            port = columns[1].text.strip()
            ip_and_port = f"{ip}:{port}"
            https = columns[6].text.strip().replace(" ", "")
            last_checked = columns[7].text.strip()
            # print(https)
            if https == "no" and not "hours" in last_checked and not "hour" in last_checked:
                if int(last_checked[0:2]) < 10 or "secs" in last_checked:
                    proxies.append(
                        {"http": "http", "ip": ip_and_port, "last_checked": last_checked})
                else:
                    continue
            else:
                continue

    return proxies


def get_proxies_with_proxy(proxy):
    url = "https://free-proxy-list.net/"
    session = HTMLSession()
    r = session.get(url, proxies={
        f"{proxy.get('http')}": f"{proxy.get('ip')}"})
    r.html.render(timeout=70)
    soup = BeautifulSoup(r.html.raw_html, "html.parser")

    table = soup.find("table", class_="table table-striped table-bordered")
    proxies = []
    for row in table.find_all("tr"):
        columns = row.find_all("td")
        if(columns != []):
            ip = columns[0].text.strip()
            port = columns[1].text.strip()
            ip_and_port = f"{ip}:{port}"
            https = columns[6].text.strip().replace(" ", "")
            last_checked = columns[7].text.strip()
            # print(https)
            if https == "no" and not "hours" in last_checked and not "hour" in last_checked:
                if int(last_checked[0:2]) < 10 or "secs" in last_checked:
                    proxies.append(
                        {"http": "http", "ip": ip_and_port, "last_checked": last_checked})
                else:
                    continue
            else:
                continue

    return proxies

