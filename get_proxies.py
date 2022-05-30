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
            # print(https)
            if https == "no":
                proxies.append({"http": "http", "ip": ip_and_port})
            else:
                continue

    return proxies
