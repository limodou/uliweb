import smtplib
from smtp import MailConnection as SmtpMailConnection

class MailConnection(SmtpMailConnection):
    def login(self):
        if self.mail_obj.user:
            self.server.ehlo()
            self.server.starttls()
            self.server.ehlo()
            self.server.login(self.mail_obj.user, self.mail_obj.password)

    def get_connection(self):
        if not self.server:
            self.server = server = smtplib.SMTP()
            self.server.connect(self.mail_obj.host or 'smtp.gmail.com', self.mail_obj.port or 587)
            self.login()
    
