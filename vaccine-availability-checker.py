import os
import time
import datetime
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
import requests
import beepy


# LOGGER
logging.basicConfig(format='%(asctime)s >>> %(message)s', level=logging.DEBUG)

# LOAD ENV
load_dotenv()

# EMAIL CONFIG
EMAIL = os.getenv('EMAIL')
EMAIL_APP_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')

# PERSONAL DETAILS
AGE = os.getenv('AGE')

# LOCATION DETAILS
PINCODE = os.getenv('PINCODE')

# API
COWIN_OPEN_API = os.getenv('COWIN_OPEN_API')

# DATE
NEXT_DAY_DATE = datetime.datetime.today() + datetime.timedelta(days=1)
NEXT_DAY_DATE_FORMATTED = NEXT_DAY_DATE.strftime('%d-%m-%Y')  # format the date to dd-mm-yyyy


def run_daemon():
    while True:
        try:
            logging.info(f'CHECKING AVAILABILITY ON [{NEXT_DAY_DATE_FORMATTED}] FOR PINCODE [{PINCODE}]')

            # Request CoWin Open API to check vaccine availability
            response = requests.get(
                url=f'{COWIN_OPEN_API}/findByPin?pincode={PINCODE}&date={NEXT_DAY_DATE_FORMATTED}',
                headers={
                    'accept': 'application/json',
                    'Accept-Language': 'hi_IN',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
                }
            ).json()

            response = filter(lambda slot: slot['min_age_limit'] <= int(AGE) and slot['available_capacity'] > 0, response['sessions'])
            response = list(response)

            # Notify user when vaccine slots are available
            if len(response) > 0:
                notify_on_screen(
                    'Vaccination Slot Available',
                    f'Woo Hoo! Vaccine is available on {NEXT_DAY_DATE_FORMATTED} for pincode {PINCODE}, '
                    f'hurry up and book the slot before its gone...')
                notify_on_email(
                    EMAIL,
                    RECEIVER_EMAIL,
                    'Vaccination Slot Available!',
                    f'Hi,\n\n'
                    f'Vaccination slot is available on {NEXT_DAY_DATE_FORMATTED} for pincode {PINCODE}, '
                    f'hurry up and book the slot before its gone...\n\n'
                    f'Visit: https://selfregistration.cowin.gov.in/\n\n'
                    f'Yours,\n'
                    f'Vaccine Availability Indicator Bot'
                )

            # Wait for three minutes to execute next request
            time.sleep(180)  # Sleep function takes time in seconds :. 180/60 = 3 Minutes
        except Exception as ex:
            # Log error and continue to the execution without stopping it
            logging.error(ex)
            pass


def notify_on_screen(title, text):
    try:
        # Show system notification
        os.system("""
                  osascript -e 'display notification "{}" with title "{}"'
                  """.format(text, title))
    except:
        logging.error('Failed to open notification popup')
    finally:
        # Play sound
        beepy.beep(sound='success')


def notify_on_email(sender, receiver, subject, body):
    try:
        logging.info('Sending email notification to the user')

        # Format Message
        msg = MIMEMultipart()
        msg['From'] = 'Vaccine Availability Checker Bot'
        msg['To'] = receiver
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Create SMTP session
        s = smtplib.SMTP('smtp.gmail.com', 587)

        # Start TLS for security
        s.starttls()

        # Authentication
        s.login(EMAIL, EMAIL_APP_PASSWORD)

        # sending the mail
        s.sendmail(from_addr=sender, to_addrs=receiver, msg=msg.as_string())

        # terminating the session
        s.quit()

        logging.info('Email notification sent to the user')
    except:
        logging.error('Failed to send email notification')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run_daemon()
