"""
Email fetching module for Gmail Rules Manager
"""

import base64
import email
from datetime import datetime
from email.utils import parsedate_to_datetime
from auth import get_gmail_service
from db import store_email, get_session
from config import MAX_EMAILS_TO_FETCH

def fetch_emails(limit=MAX_EMAILS_TO_FETCH):
    """
    Fetch emails from Gmail API and store them in the database.
    
    Args:
        limit (int): Maximum number of emails to fetch
        
    Returns:
        list: List of email IDs that were fetched
    """
    # Get authenticated Gmail API service
    service = get_gmail_service()
    
    # Get list of messages
    results = service.users().messages().list(
        userId='me',
        maxResults=limit,
        labelIds=['INBOX']
    ).execute()
    
    messages = results.get('messages', [])
    
    if not messages:
        print("No messages found.")
        return []
    
    email_ids = []
    
    # Process each message
    for message in messages:
        msg_id = message['id']
        
        # Get the message details
        msg = service.users().messages().get(
            userId='me', 
            id=msg_id,
            format='full'
        ).execute()
        
        # Parse and store the email
        email_data = parse_email(msg)
        
        # Store in database - this function creates its own session
        stored_email = store_email(email_data)
        if stored_email:
            email_ids.append(stored_email.id)
    
    return email_ids

def parse_email(msg):
    """
    Parse email message from Gmail API response.
    
    Args:
        msg (dict): Message dict from Gmail API
        
    Returns:
        dict: Parsed email data
    """
    # Get headers
    headers = {header['name']: header['value'] for header in msg['payload']['headers']}
    
    # Parse received date
    received_date = None
    if 'Date' in headers:
        try:
            received_date = parsedate_to_datetime(headers['Date'])
        except:
            received_date = datetime.utcnow()
    
    # Get labels
    labels = ','.join(msg.get('labelIds', []))
    
    # Check if the email has been read
    is_read = 'UNREAD' not in msg.get('labelIds', [])
    
    # Get message body
    body_text = None
    body_html = None
    
    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                body_text = base64.urlsafe_b64decode(
                    part['body']['data'].encode('ASCII')
                ).decode('utf-8')
            elif part['mimeType'] == 'text/html' and 'data' in part['body']:
                body_html = base64.urlsafe_b64decode(
                    part['body']['data'].encode('ASCII')
                ).decode('utf-8')
    elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
        body_data = base64.urlsafe_b64decode(
            msg['payload']['body']['data'].encode('ASCII')
        ).decode('utf-8')
        
        if msg['payload']['mimeType'] == 'text/plain':
            body_text = body_data
        elif msg['payload']['mimeType'] == 'text/html':
            body_html = body_data
    
    # Create email data dictionary
    email_data = {
        'message_id': msg['id'],
        'thread_id': msg['threadId'],
        'from_address': headers.get('From', ''),
        'to_address': headers.get('To', ''),
        'subject': headers.get('Subject', '(No Subject)'),
        'snippet': msg.get('snippet', ''),
        'body_text': body_text,
        'body_html': body_html,
        'received_date': received_date,
        'is_read': is_read,
        'labels': labels
    }
    
    return email_data