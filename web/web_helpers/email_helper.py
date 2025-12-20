import os
import smtplib
from dotenv import load_dotenv, find_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path
from datetime import datetime

# Email configuration and methods for updating email list with details provided from bot

# Environment Variables
load_dotenv(find_dotenv(".env"))

# SMTP credentials
SMTP_HOST     = os.getenv("SMTP_HOST", "")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 0))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PWD      = os.getenv("SMTP_PWD", "")

# email configuration
EMAIL_NAME = os.getenv("EMAIL_NAME")
EMAIL_ADDR = os.getenv("EMAIL_ADDR")
DOMAIN     = os.getenv("DOMAIN")
BASE_DIR   = Path(__file__).parent.parent

# Email helper methods

def send_email(msg: MIMEMultipart):
    # Sends message to email list
    recipients = os.getenv("NOTIFY_EMAILS", "").split(",")

    # log in to smtp server and send email
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USERNAME, SMTP_PWD)
        for address in recipients:
            msg["To"] = address
            smtp.sendmail(EMAIL_ADDR, address, msg.as_string())

def get_template(file_name):
    # Fetches template from directory
    template_path = BASE_DIR / "templates" / file_name
    return template_path.read_text()

def construct_message(time_stamp, html_body):
    # Constructs MIME message

    # formats date
    data     = datetime.fromtimestamp(time_stamp)
    time_str = data.strftime("%H:%M")
    html_body = html_body.replace("{{ time }}", time_str)

    # construct message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Watered (WALTER) {time_str}"
    msg["From"]    = formataddr((EMAIL_NAME, EMAIL_ADDR))

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    return msg

# Email message formatters

def send_success_email(time_stamp):
    # Sends success email to email list, first loads in templates and formats with passed data and then sends with SMTP

    # load template
    html_template = get_template("water-email.html")

    # format template
    html_body = html_template.replace("{{ domain }}", DOMAIN)

    # construct message
    msg = construct_message(time_stamp, html_body)

    # send message
    send_email(msg)

def send_error_email(time_stamp, error_msg):
    # Send error email to email list

    # load template
    html_template = get_template("error-email.html")

    # format template
    html_body = (html_template
                 .replace("{{ domain }}", DOMAIN)
                 .replace("{{ error_msg }}", error_msg))

    # construct message
    msg = construct_message(time_stamp, html_body)

    # send message
    send_email(msg)

