"""
Configuration settings for the Gmail Rules Manager
"""

import os

# File paths
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
RULES_FILE = 'rules.json'

# Gmail API settings
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Read-only access initially
    'https://www.googleapis.com/auth/gmail.modify',  # Will be needed later for marking as read/unread
    'https://www.googleapis.com/auth/gmail.labels',  # Will be needed for moving messages
]

# Database settings
DATABASE_URL = 'sqlite:///emails.db'

# Email fetching settings
MAX_EMAILS_TO_FETCH = 20  # Limit the number of emails to fetch initially

# Whether to perform actions or just simulate them
DRY_RUN = False  # Set to False to actually perform actions