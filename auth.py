"""
Authentication module for Gmail API
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE

def get_gmail_service():
    """
    Authenticate with Gmail API and return the service object.
    
    This function handles the OAuth2 flow, including:
    - Loading existing credentials from token.json if available
    - Refreshing credentials if expired
    - Initiating the OAuth flow if no valid credentials exist
    
    Returns:
        The authenticated Gmail API service object
    """
    creds = None
    
    # Check if token file exists with stored credentials
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    # Build and return the Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service