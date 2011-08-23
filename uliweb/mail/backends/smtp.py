import smtplib
from uliweb.mail import BaseMailConnection

class MailConnection(BaseMailConnection):
    def __init__(self, mail_obj):
        self.mail_obj = mail_obj
        self.server = None
        
    def login(self):
        if self.mail_obj.user:
            self.server.login(self.mail_obj.user, self.mail_obj.password)
        
    def get_connection(self):
        if not self.server:
            self.server = server = smtplib.SMTP()
            self.server.connect(self.mail_obj.host, self.mail_obj.port)
#            server.ehlo()
#            server.starttls()
#            server.ehlo()
            self.login()
    
    def send_mail(self, from_, to_, message):
        self.server.sendmail(from_, to_, str(message))
    
    def close(self):
        if self.server:
            self.server.close()
            self.server = None
    