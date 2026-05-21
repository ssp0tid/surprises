"""SMTP client for sending emails."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmailRecipient:
    """Represents an email recipient."""
    email: str
    name: str = ""


class SMTPClient:
    """SMTP client for sending emails."""
    
    def __init__(self, server: str, port: int, use_tls: bool, username: str, password: str):
        self.server = server
        self.port = port
        self.use_tls = use_tls
        self.username = username
        self.password = password
        self.connection: Optional[smtplib.SMTP] = None
    
    def connect(self) -> bool:
        """Connect to the SMTP server."""
        try:
            self.connection = smtplib.SMTP(self.server, self.port)
            self.connection.ehlo()
            
            if self.use_tls:
                self.connection.starttls()
                self.connection.ehlo()
            
            self.connection.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"SMTP connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the SMTP server."""
        if self.connection:
            try:
                self.connection.quit()
            except:
                pass
            self.connection = None
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_name: str = "",
        cc: str = "",
        is_html: bool = False
    ) -> bool:
        """Send an email."""
        if not self.connection:
            if not self.connect():
                return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_name if from_name else self.username
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = cc
            
            # Attach body
            content_type = 'html' if is_html else 'plain'
            mime_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, mime_type))
            
            # Get recipients
            recipients = [to_email]
            if cc:
                recipients.append(cc)
            
            self.connection.sendmail(
                self.username,
                recipients,
                msg.as_string()
            )
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False