import ssl
import smtplib

from pynotifier import NotificationClient, Notification
from pynotifier.backends import platform, smtp

smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context())

c = NotificationClient()

c.register_backend(platform.Backend())
c.register_backend(smtp.Backend(server=smtp_server,
                                name='My Organization',
                                email='sender@organization.com',
                                password='super_password'))

filenames = [
  'path/to/file1.json',
  'path/to/file2.txt',
  # ...
]

attachments = []
for filename in filenames:
	attachments.append(smtp.Attachment(open(filename, 'rb'), filename))

smtp_config = smtp.NotificationConfig(emails=['receiver_1@email.com', 'receiver_2@email.com'],
                                      attachments=attachments)
notification = Notification(title='Hello', message='World', smtp=smtp_config)

c.notify_all(notification)
