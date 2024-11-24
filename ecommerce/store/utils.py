# utils.py

from django.core.mail import EmailMessage
import os

class Util:
    @staticmethod
    def send_email(data):
        try:
            email = EmailMessage(
                subject=data['subject'],
                body=data['body'],
                from_email=os.environ.get('EMAIL_FROM', 'default_from_email@example.com'),
                to=[data['to_email']]
            )
            email.send()
        except Exception as e:
            print(f"Error sending email: {str(e)}")
