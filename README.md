# Gmail Rules Manager

A standalone Python script that integrates with Gmail API and performs rule-based operations on emails.

## Features

- Authenticates to Google's Gmail API using OAuth
- Fetches emails from your Gmail inbox
- Stores emails in a SQLite database
- Processes emails based on configurable rules
- Supports various conditions and actions:
  - **Conditions**: From, Subject, Message, Received Date/Time
  - **String Predicates**: Contains, Does not Contain, Equals, Does not equal
  - **Date Predicates**: Less than, Greater than (days/months)
  - **Actions**: Mark as read/unread, Move message

## Prerequisites

- Python 3.6 or higher
- Google account with Gmail
- Google Cloud Platform project with Gmail API enabled

## Installation

1. Clone the repository:

```bash
git clone git@github.com:akshyv/gmail-rules-manager.git
cd gmail-rules-manager
```

2. Create a virtual environment and activate it:

```bash
python -m venv gmail-rules-env
source gmail-rules-env/bin/activate  # On Windows: gmail-rules-env\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Set up Google Cloud Platform:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Gmail API for your project
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials JSON file and save it as `credentials.json` in the project directory

## Configuration

### OAuth Scopes

By default, the application uses the following OAuth scopes:

- `https://www.googleapis.com/auth/gmail.readonly` - Read-only access (for fetching emails)

When you're ready to perform actions on emails, uncomment the following scopes in `config.py`:

- `https://www.googleapis.com/auth/gmail.modify` - For marking emails as read/unread
- `https://www.googleapis.com/auth/gmail.labels` - For moving messages between labels

### Rules Configuration

Rules are defined in the `rules.json` file. Each rule consists of:

- `id`: Unique identifier for the rule
- `name`: Human-readable name for the rule
- `predicate`: How to combine conditions (`all` or `any`)
- `conditions`: List of conditions to check
- `actions`: List of actions to perform when conditions match

Example rule:

```json
{
  "id": "important-financial-emails",
  "name": "Important Financial Emails",
  "predicate": "all",
  "conditions": [
    {
      "field": "from",
      "predicate": "contains",
      "value": "bank"
    },
    {
      "field": "subject",
      "predicate": "contains",
      "value": "statement"
    }
  ],
  "actions": [
    {
      "type": "mark_as_read"
    },
    {
      "type": "move_message",
      "destination": "Financial"
    }
  ]
}
```

## Usage

### Fetching Emails

To fetch emails from Gmail and store them in the database:

```bash
python main.py --fetch --limit 10
```

This will fetch the 10 most recent emails from your inbox.

### Processing Emails with Rules

To process emails with your defined rules:

```bash
python main.py --process
```

To process only the emails that were just fetched:

```bash
python main.py --fetch --process --limit 10
```

### Dry Run Mode

By default, the application runs in "dry run" mode, which simulates actions without actually performing them. To disable dry run mode and perform actual actions, modify the `DRY_RUN` setting in `config.py` or use the `--dry-run` flag:

```bash
python main.py --process --dry-run
```

### Verbose Output

For more detailed output:

```bash
python main.py --process --verbose
```

## Database

The application uses SQLite to store email data. The database file `emails.db` is created automatically when you first run the application.

The database schema includes:

- `emails` table: Stores email metadata and content
- `action_logs` table: Records actions performed on emails

## Acknowledgements

- Google Gmail API
- SQLAlchemy
- Python OAuth2 Client