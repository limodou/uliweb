#######################################
#
# Send mail
# Known smtp server: smtp.gmail.com, 587
#######################################
import os
import mimetypes
import email
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEAudio import MIMEAudio
from email.MIMEImage import MIMEImage
from email.Encoders import encode_base64
from email.header import Header

class BaseMailConnection(object):
    def __init__(self, mail_obj):
        self.mail_obj = self.mail_obj
        
    def get_connection(self, mail_obj):
        raise NotImplementedError, "This function is not implemented yet"

    def send_mail(self, from_, to_, message):
        raise NotImplementedError, "This function is not implemented yet"
    
    def close(self):
        pass
   
class EmailMessage(object):
    def __init__(self, from_, to_, subject, message, cc_=None,html=False, encoding='utf-8', attachments=None):
        from uliweb.utils.common import simple_value
        
        self.from_ = from_
        self.to_ = to_
        self.encoding = encoding
        self.subject = simple_value(subject, encoding)
        self.message = simple_value(message, encoding)
        self.attachments = attachments or []
        self.html = html
        
        self.msg = msg = MIMEMultipart()
        msg['From'] = from_
        msg['To'] = to_
        if cc_:
            msg['CC'] = cc_
        msg['Subject'] = Header(self.subject, self.encoding)
        if html:
            content_type = 'html'
        else:
            content_type = 'plain'
        msg.attach(MIMEText(self.message, content_type, self.encoding))
        
        for f in self.attachments:
            msg.attach(self.getAttachment(f))
            
    def attach(self, filename):
        self.msg.attach(self.getAttachment(filename))
        
    def getAttachment(self, attachmentFilePath):
        contentType, encoding = mimetypes.guess_type(attachmentFilePath)
        if contentType is None or encoding is not None:
            contentType = 'application/octet-stream'
        mainType, subType = contentType.split('/', 1)
        file = open(attachmentFilePath, 'rb')
        if mainType == 'text':
            attachment = MIMEText(file.read())
#        elif mainType == 'html':
#            attachment = MIMEText(file.read(), 'html')
        elif mainType == 'message':
            attachment = email.message_from_file(file)
        elif mainType == 'image':
            attachment = MIMEImage(file.read(),_subType=subType)
        elif mainType == 'audio':
            attachment = MIMEAudio(file.read(),_subType=subType)
        else:
            attachment = MIMEBase(mainType, subType)
            attachment.set_payload(file.read())
            encode_base64(attachment)
        file.close()
        attachment.add_header('Content-Disposition', 'attachment',   filename=os.path.basename(attachmentFilePath))
        return attachment
    
    def __str__(self):
        return self.msg.as_string()
        
class Mail(object):
    def __init__(self, host=None, port=None, user=None, password=None, backend=None, sendmail_location=None):
        from uliweb import settings
        from uliweb.utils.common import import_attr
        
        self.host = host or settings.get_var('MAIL/HOST')
        self.port = port or settings.get_var('MAIL/PORT', 25)
        self.user = user or settings.get_var('MAIL/USER')
        self.password = password or settings.get_var('MAIL/PASSWORD')
        self.backend = backend or settings.get_var('MAIL/BACKEND', 'uliweb.mail.backends.smtp')
        self.sendmail_location = sendmail_location or settings.get_var('MAIL/SENDMAIL_LOCATION', '/usr/sbin/sendmail')
        cls = import_attr(self.backend + '.MailConnection')
        self.con = cls(self)
        
    def send_mail(self, from_, to_, subject, message, cc_=None, html=False, attachments=None):
        #process to_
        if isinstance(to_, (str, unicode)):
            send_to = to_.split(',')
        elif isinstance(to_, (tuple, list)):
            send_to = to_
            to_ = ','.join(send_to)
        
        if isinstance(cc_, (str, unicode)):
            cc_list = cc_.split(',')
        elif isinstance(cc_, (tuple, list)):
            cc_list = cc_
            cc_ = ','.join(cc_) #should be changed to string
        else:
            cc_list = None
        if cc_list:
            send_to += cc_list
        
        email = EmailMessage(from_, to_, subject, message, cc_=cc_, html=html, attachments=attachments)
        self.con.get_connection()
        self.con.send_mail(from_, send_to, email)
        self.con.close()
