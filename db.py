"""
Database operations for Gmail Rules Manager
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import DATABASE_URL

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Email(Base):
    """Email table to store email metadata"""
    __tablename__ = 'emails'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(255), unique=True, nullable=False)  # Gmail's unique message ID
    thread_id = Column(String(255))
    from_address = Column(String(255))
    to_address = Column(Text)  # Could have multiple recipients
    subject = Column(String(500))
    snippet = Column(Text)  # Gmail provides a snippet of the message
    body_text = Column(Text, nullable=True)  # Full message text (if available)
    body_html = Column(Text, nullable=True)  # HTML version (if available)
    received_date = Column(DateTime)
    is_read = Column(Boolean, default=False)
    labels = Column(Text)  # Store labels as comma-separated string
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Email(id={self.id}, from='{self.from_address}', subject='{self.subject}')>"

class ActionLog(Base):
    """Log of actions performed on emails"""
    __tablename__ = 'action_logs'
    
    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey('emails.id'))
    action_type = Column(String(50))  # e.g., 'mark_read', 'move_message'
    rule_id = Column(String(50))  # ID of the rule that triggered this action
    action_details = Column(Text)  # Additional details about the action
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    email = relationship("Email")
    
    def __repr__(self):
        return f"<ActionLog(id={self.id}, action='{self.action_type}', success={self.success})>"

def init_db():
    """Initialize the database by creating all tables if they don't exist"""
    Base.metadata.create_all(engine)

def get_session():
    """Return a new database session"""
    return Session()

def store_email(email_data):
    """
    Store an email in the database.
    
    Args:
        email_data (dict): Dictionary containing email data
        
    Returns:
        Email: The created or updated Email object
    """
    session = get_session()
    
    try:
        # Check if email already exists
        existing_email = session.query(Email).filter_by(
            message_id=email_data['message_id']
        ).first()
        
        if existing_email:
            # Update existing email
            for key, value in email_data.items():
                if hasattr(existing_email, key):
                    setattr(existing_email, key, value)
            email = existing_email
        else:
            # Create new email
            email = Email(**email_data)
            session.add(email)
        
        session.commit()
        
        # Get ID before closing session
        email_id = email.id
        
        # Create a new Email object with just the ID to return
        # This avoids the "not bound to a Session" error
        return_email = Email(id=email_id)
        
        return return_email
    
    except Exception as e:
        session.rollback()
        print(f"Error storing email: {e}")
        return None
    
    finally:
        session.close()

def log_action(email_id, action_type, rule_id, action_details, success=True, error_message=None):
    """
    Log an action performed on an email.
    
    Args:
        email_id (int): ID of the email
        action_type (str): Type of action performed
        rule_id (str): ID of the rule that triggered the action
        action_details (str): Additional details about the action
        success (bool): Whether the action was successful
        error_message (str): Error message if the action failed
        
    Returns:
        ActionLog: The created ActionLog object
    """
    session = get_session()
    
    try:
        log = ActionLog(
            email_id=email_id,
            action_type=action_type,
            rule_id=rule_id,
            action_details=action_details,
            success=success,
            error_message=error_message
        )
        
        session.add(log)
        session.commit()
        
        # Get ID before closing session
        log_id = log.id
        
        # Create a new ActionLog object with just the ID to return
        # This avoids the "not bound to a Session" error
        return_log = ActionLog(id=log_id)
        
        return return_log
    
    except Exception as e:
        session.rollback()
        print(f"Error logging action: {e}")
        return None
    
    finally:
        session.close()

def get_email_by_id(email_id):
    """
    Get an email by ID.
    
    Args:
        email_id (int): ID of the email
        
    Returns:
        Email: The Email object, or None if not found
    """
    session = get_session()
    
    try:
        return session.query(Email).filter_by(id=email_id).first()
    
    finally:
        session.close()