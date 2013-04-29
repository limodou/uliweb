import smtplib
from smtp import MailConnection as SmtpMailConnection

class MailConnection(SmtpMailConnection):
    def login(self):
        pass

    def get_connection(self):
        pass
            
    def send_mail(self, from_, to_, message):
        from subprocess import Popen, PIPE
        
        p = Popen([self.sendmail_location, "-t"], stdin=PIPE)
        p.communicate(str(message))
    
    def close(self):
        pass
