"""IMAP client for fetching and managing emails."""

import imaplib
import email
from email.parser import Parser
from email.policy import default
from dataclasses import dataclass
from typing import List, Optional, Tuple
import re


@dataclass
class EmailMessage:
    """Represents an email message."""
    uid: str
    subject: str
    sender: str
    date: str
    body: str = ""
    to: str = ""
    cc: str = ""
    read: bool = False


class IMAPClient:
    """IMAP client for connecting to email servers."""
    
    def __init__(self, server: str, port: int, use_ssl: bool, username: str, password: str):
        self.server = server
        self.port = port
        self.use_ssl = use_ssl
        self.username = username
        self.password = password
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """Connect to the IMAP server."""
        try:
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.server, self.port)
            else:
                self.connection = imaplib.IMAP4(self.server, self.port)
            
            self.connection.login(self.username, self.password)
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the IMAP server."""
        if self.connection:
            try:
                self.connection.logout()
            except:
                pass
            self.connection = None
            self.is_connected = False
    
    def _parse_email_address(self, addr_str: str) -> str:
        """Parse email address from header value."""
        if not addr_str:
            return ""
        # Extract email from "Name <email>" format
        match = re.search(r'<(.+?)>', addr_str)
        if match:
            return match.group(1)
        match = re.search(r'[\w\.-]+@[\w\.-]+', addr_str)
        if match:
            return match.group()
        return addr_str
    
    def _get_folder_list(self) -> List[str]:
        """Get list of available folders."""
        if not self.is_connected:
            return []
        
        try:
            status, folders = self.connection.list()
            if status != 'OK':
                return []
            
            folder_list = []
            for folder in folders:
                # Parse folder name from response
                if isinstance(folder, bytes):
                    folder = folder.decode('utf-8')
                # Extract folder name (in quotes)
                match = re.search(r'"([^"]+)"', folder)
                if match:
                    folder_list.append(match.group(1))
                else:
                    parts = folder.split()
                    if len(parts) > 2:
                        folder_list.append(parts[-1])
            
            return folder_list
        except Exception as e:
            print(f"Error listing folders: {e}")
            return []
    
    def get_folders(self) -> List[Tuple[str, int]]:
        """Get folders with message counts."""
        if not self.is_connected:
            return []
        
        folders = self._get_folder_list()
        result = []
        
        for folder in folders:
            try:
                status, data = self.connection.status(folder, '(MESSAGES UNSEEN)')
                if status == 'OK' and data:
                    match = re.search(r'MESSAGES (\d+)', data[0].decode() if isinstance(data[0], bytes) else str(data[0]))
                    count = int(match.group(1)) if match else 0
                    result.append((folder, count))
            except:
                result.append((folder, 0))
        
        return result
    
    def select_folder(self, folder: str = "INBOX") -> bool:
        """Select a folder."""
        if not self.is_connected:
            return False
        
        try:
            status, data = self.connection.select(folder)
            return status == 'OK'
        except Exception as e:
            print(f"Error selecting folder: {e}")
            return False
    
    def fetch_emails(self, folder: str = "INBOX", limit: int = 50) -> List[EmailMessage]:
        """Fetch emails from a folder."""
        if not self.is_connected:
            return []
        
        emails = []
        
        if not self.select_folder(folder):
            return []
        
        try:
            # Get UIDs instead of message numbers
            status, data = self.connection.uid('search', None, 'ALL')
            if status != 'OK':
                return []
            
            uids = data[0].split()
            if not uids:
                return []
            
            # Get most recent emails (limit)
            uids = uids[-limit:]
            
            for uid in reversed(uids):
                try:
                    status, msg_data = self.connection.uid('fetch', uid, '(BODY.PEEK[HEADER.FIELDS])')
                    if status != 'OK' or not msg_data:
                        continue
                    
                    raw_email = msg_data[0][1]
                    if isinstance(raw_email, bytes):
                        raw_email = raw_email.decode('utf-8', errors='replace')
                    
                    parser = Parser(policy=default)
                    msg = parser.parsestr(raw_email)
                    
                    subject = msg.get('Subject', '(No Subject)')
                    from_header = msg.get('From', '')
                    date = msg.get('Date', '')
                    
                    # Get unique ID
                    uid_str = uid.decode() if isinstance(uid, bytes) else str(uid)
                    
                    email_msg = EmailMessage(
                        uid=uid_str,
                        subject=subject,
                        sender=self._parse_email_address(from_header),
                        date=date,
                        to=self._parse_email_address(msg.get('To', '')),
                        cc=self._parse_email_address(msg.get('Cc', ''))
                    )
                    emails.append(email_msg)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error fetching emails: {e}")
        
        return emails
    
    def fetch_email_body(self, uid: str, folder: str = "INBOX") -> Optional[str]:
        """Fetch full email body."""
        if not self.is_connected:
            return None
        
        if not self.select_folder(folder):
            return None
        
        try:
            status, msg_data = self.connection.uid('fetch', uid, '(RFC822)')
            if status != 'OK' or not msg_data:
                return None
            
            raw_email = msg_data[0][1]
            if isinstance(raw_email, bytes):
                raw_email = raw_email.decode('utf-8', errors='replace')
            
            parser = Parser(policy=default)
            msg = parser.parsestr(raw_email)
            
            # Get body
            if msg.is_multipart():
                # Try to get text/plain, then text/html
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        return part.get_payload(decode=True).decode('utf-8', errors='replace')
                    primary_body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                return primary_body
            else:
                return msg.get_payload(decode=True).decode('utf-8', errors='replace')
                
        except Exception as e:
            print(f"Error fetching body: {e}")
            return None
    
    def delete_email(self, uid: str, folder: str = "INBOX") -> bool:
        """Move email to Trash."""
        if not self.is_connected:
            return False
        
        if not self.select_folder(folder):
            return False
        
        try:
            # First copy to Trash, then mark for deletion
            status, _ = self.connection.uid('COPY', uid, 'Trash')
            if status == 'OK':
                status, _ = self.connection.uid('STORE', uid, '+FLAGS', '\\Deleted')
                return status == 'OK'
            return False
        except Exception as e:
            print(f"Error deleting email: {e}")
            return False
    
    def search_emails(self, query: str, folder: str = "INBOX") -> List[EmailMessage]:
        """Search emails by query."""
        if not self.is_connected:
            return []
        
        if not self.select_folder(folder):
            return []
        
        try:
            # Search in subject and from fields
            query = query.encode('utf-8')
            status, data = self.connection.uid('search', None, f'(SUBJECT "{query.decode()}" OR FROM "{query.decode()}")')
            
            if status != 'OK':
                return []
            
            uids = data[0].split()
            if not uids:
                return []
            
            emails = []
            for uid in reversed(uids):
                try:
                    status, msg_data = self.connection.uid('fetch', uid, '(BODY.PEEK[HEADER.FIELDS])')
                    if status != 'OK' or not msg_data:
                        continue
                    
                    raw_email = msg_data[0][1]
                    if isinstance(raw_email, bytes):
                        raw_email = raw_email.decode('utf-8', errors='replace')
                    
                    parser = Parser(policy=default)
                    msg = parser.parsestr(raw_email)
                    
                    subject = msg.get('Subject', '(No Subject)')
                    from_header = msg.get('From', '')
                    date = msg.get('Date', '')
                    
                    uid_str = uid.decode() if isinstance(uid, bytes) else str(uid)
                    
                    email_msg = EmailMessage(
                        uid=uid_str,
                        subject=subject,
                        sender=self._parse_email_address(from_header),
                        date=date,
                        to=self._parse_email_address(msg.get('To', '')),
                        cc=self._parse_email_address(msg.get('Cc', ''))
                    )
                    emails.append(email_msg)
                    
                except:
                    continue
            
            return emails
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def move_email(self, uid: str, target_folder: str, source_folder: str = "INBOX") -> bool:
        """Move email to another folder."""
        if not self.is_connected:
            return False
        
        if not self.select_folder(source_folder):
            return False
        
        try:
            status, _ = self.connection.uid('COPY', uid, target_folder)
            if status == 'OK':
                status, _ = self.connection.uid('STORE', uid, '+FLAGS', '\\Deleted')
                return status == 'OK'
            return False
        except Exception as e:
            print(f"Error moving email: {e}")
            return False