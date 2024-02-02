import smtplib, logging, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Optional


SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER_NAME="profiletemp66@gmail.com"
SMTP_PASSWORD="rcvgecikrvjgwldg"


def send_email(to_address, subject, message_body, image_path: Optional[str] = None):
    try :
        smtp_server = SMTP_SERVER
        smtp_port = SMTP_PORT
        smtp_username = SMTP_USER_NAME
        smtp_password = SMTP_PASSWORD

        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_address
        msg['Subject'] = subject

        # Attach the HTML message with CSS styling
        msg.attach(MIMEText(message_body, 'html'))

        # Attach the image
        if image_path:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                image = MIMEImage(image_data, name=os.path.basename(image_path))
                msg.attach(image)

        # Connect to the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)

            # Send the email
            server.sendmail(smtp_username, to_address, msg.as_string())

        logging.info("[MAIL_UTIL][Email sent successfully!]")

    except Exception as ex :
        logging.exception("[MAIL_UTIL][Exception in send_email] {} ".format(ex))