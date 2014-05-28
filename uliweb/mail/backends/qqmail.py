# -*- coding: utf-8 -*-
###############################################################################
# file    : qqmail.py
# author  : wangyubin
# date    : Fri May 23 16:53:17 2014
#
# brief   : qqmail backend
# history : init
###############################################################################

import smtplib
from .smtp import MailConnection as SmtpMailConnection

class MailConnection(SmtpMailConnection):
    def login(self):
        if self.mail_obj.user:
            self.server.login(self.mail_obj.user, self.mail_obj.password)

    def get_connection(self):
        if not self.server:
            self.server = server = smtplib.SMTP_SSL()
            self.server.connect(self.mail_obj.host or 'smtp.qq.com', self.mail_obj.port or 465)
            self.login()