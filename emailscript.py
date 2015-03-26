'''
This script is just used to send me an alert if there has been a donation. Since people are allowed to request things via donations,
I need to check the email to see if there were any requests. Just a simple email to do this.
'''

import smtplib

msg = 'Got a donation success, check.'
server = smtplib.SMTP('smtp.gmail.com',587) #port 587 or 465
server.ehlo()
server.starttls()
server.ehlo()
server.login('','')
server.sendmail('','',msg)
server.close()
