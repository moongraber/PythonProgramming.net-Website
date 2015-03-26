import smtplib


msg = 'Got a donation success, check.'
server = smtplib.SMTP('smtp.gmail.com',587) #port 587 or 465
server.ehlo()
server.starttls()
server.ehlo()
server.login('','')
server.sendmail('','',msg)
server.close()
