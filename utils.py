import os
import smtplib
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv, find_dotenv


def scrap_with_render(url, session, timeout=70, sleep=0, wait=0.2, ip=None):
    try:
        s = session
        r = s.get(url, proxies={f"http": f"{ip}"})
        r.html.render(timeout=timeout, sleep=sleep, wait=wait)
        soup = BeautifulSoup(r.html.raw_html, "html.parser")
        return soup
    except:
        print("Error scraping")


def get_dates():
    today = date.today().day
    tomorrow = today + 1
    now = datetime.now().time().strftime("%H:%M")
    now = timedelta(hours=int(now[:2]), minutes=int(now[3:]), seconds=0)
    return today, tomorrow, now


def send_mail(subject, message_to_send):
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

    try:
        load_dotenv(find_dotenv())
        sender_address = os.getenv("SENDER_ADDRESS")
        sender_pass = os.getenv("SENDER_PASS")
        receiver_address = os.getenv("RECEIVER_ADDRESS")

        message = MIMEMultipart('alternative')
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = subject

        html = html.format(message_to_send)

        message.attach(MIMEText(html, 'html'))

        session = smtplib.SMTP('smtp.sendgrid.net', 465)
        session.starttls()
        session.login(sender_address, sender_pass)
        text = message.as_string()
        session.sendmail(sender_address, receiver_address, text)
        session.quit()
        print("Email sent!")
    except:
        print("Error sending mail")


def remove_duplicates(list):
    return [i for n, i in enumerate(list) if i not in list[n+1:]]


def clean_text(text, words_to_remove, word_to_replace="", lower=True):
    if lower:
        text = text.lower().strip()
    for word in words_to_remove:
        text = text.replace(word, word_to_replace)
    return text
