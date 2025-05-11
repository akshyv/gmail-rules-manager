"""
Actions module for Gmail Rules Manager
"""

from auth import get_gmail_service
from db import get_session, Email, log_action, get_email_by_id
from config import DRY_RUN

def execute_actions(email_actions):
    """
    Execute actions on emails.
    
    Args:
        email_actions (dict): Dictionary mapping email IDs to applicable actions
        
    Returns:
        dict: Dictionary mapping email IDs to action results
    """
    results = {}
    
    for email_id, actions in email_actions.items():
        results[email_id] = []
        
        for action_info in actions:
            action = action_info['action']
            rule_id = action_info['rule_id']
            
            action_type = action['type']
            result = None
            
            # Execute the appropriate action
            if action_type == 'mark_as_read':
                result = mark_as_read(email_id, rule_id)
            elif action_type == 'mark_as_unread':
                result = mark_as_unread(email_id, rule_id)
            elif action_type == 'move_message':
                destination = action.get('destination', '')
                result = move_message(email_id, destination, rule_id)
            else:
                result = {
                    'success': False,
                    'message': f"Unknown action type: {action_type}"
                }
            
            results[email_id].append(result)
    
    return results

def mark_as_read(email_id, rule_id):
    """
    Mark an email as read.
    
    Args:
        email_id (int): ID of the email in the database
        rule_id (str): ID of the rule that triggered this action
        
    Returns:
        dict: Result of the action
    """
    session = get_session()
    
    try:
        # Get email from database
        email = session.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            return {
                'success': False,
                'message': f"Email with ID {email_id} not found"
            }
        
        # Store necessary data before closing session
        message_id = email.message_id
        subject = email.subject
        is_already_read = email.is_read
        
    finally:
        session.close()
    
    # Proceed with the action
    if DRY_RUN:
        log_action(email_id, 'mark_as_read', rule_id, 
                  f"Would mark email '{subject}' as read (DRY RUN)")
        
        return {
            'success': True,
            'message': f"Would mark email '{subject}' as read (DRY RUN)"
        }
    
    # If email is already read, skip
    if is_already_read:
        log_action(email_id, 'mark_as_read', rule_id, 
                  f"Email '{subject}' is already marked as read")
        
        return {
            'success': True,
            'message': f"Email is already marked as read"
        }
    
    try:
        # Mark as read in Gmail
        service = get_gmail_service()
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        # Update database
        session = get_session()
        try:
            email = session.query(Email).filter(Email.id == email_id).first()
            if email:
                email.is_read = True
                session.commit()
        finally:
            session.close()
        
        # Log action
        log_action(email_id, 'mark_as_read', rule_id, 
                  f"Marked email '{subject}' as read")
        
        return {
            'success': True,
            'message': f"Marked email as read"
        }
    
    except Exception as e:
        # Log error
        log_action(email_id, 'mark_as_read', rule_id, 
                  f"Failed to mark email as read", 
                  success=False, 
                  error_message=str(e))
        
        return {
            'success': False,
            'message': f"Error: {str(e)}"
        }

def mark_as_unread(email_id, rule_id):
    """
    Mark an email as unread.
    
    Args:
        email_id (int): ID of the email in the database
        rule_id (str): ID of the rule that triggered this action
        
    Returns:
        dict: Result of the action
    """
    session = get_session()
    
    try:
        # Get email from database
        email = session.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            return {
                'success': False,
                'message': f"Email with ID {email_id} not found"
            }
        
        # Store necessary data before closing session
        message_id = email.message_id
        subject = email.subject
        is_already_unread = not email.is_read
        
    finally:
        session.close()
    
    # Proceed with the action
    if DRY_RUN:
        log_action(email_id, 'mark_as_unread', rule_id, 
                  f"Would mark email '{subject}' as unread (DRY RUN)")
        
        return {
            'success': True,
            'message': f"Would mark email '{subject}' as unread (DRY RUN)"
        }
    
    # If email is already unread, skip
    if is_already_unread:
        log_action(email_id, 'mark_as_unread', rule_id, 
                  f"Email '{subject}' is already marked as unread")
        
        return {
            'success': True,
            'message': f"Email is already marked as unread"
        }
    
    try:
        # Mark as unread in Gmail
        service = get_gmail_service()
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': ['UNREAD']}
        ).execute()
        
        # Update database
        session = get_session()
        try:
            email = session.query(Email).filter(Email.id == email_id).first()
            if email:
                email.is_read = False
                session.commit()
        finally:
            session.close()
        
        # Log action
        log_action(email_id, 'mark_as_unread', rule_id, 
                  f"Marked email '{subject}' as unread")
        
        return {
            'success': True,
            'message': f"Marked email as unread"
        }
    
    except Exception as e:
        # Log error
        log_action(email_id, 'mark_as_unread', rule_id, 
                  f"Failed to mark email as unread", 
                  success=False, 
                  error_message=str(e))
        
        return {
            'success': False,
            'message': f"Error: {str(e)}"
        }

def move_message(email_id, destination, rule_id):
    """
    Move an email to a different label.
    
    Args:
        email_id (int): ID of the email in the database
        destination (str): Destination label
        rule_id (str): ID of the rule that triggered this action
        
    Returns:
        dict: Result of the action
    """
    session = get_session()
    
    try:
        # Get email from database
        email = session.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            return {
                'success': False,
                'message': f"Email with ID {email_id} not found"
            }
        
        # Store necessary data before closing session
        message_id = email.message_id
        subject = email.subject
        current_labels = email.labels.split(',') if email.labels else []
        
    finally:
        session.close()
    
    # Proceed with the action
    if DRY_RUN:
        log_action(email_id, 'move_message', rule_id, 
                  f"Would move email '{subject}' to '{destination}' (DRY RUN)")
        
        return {
            'success': True,
            'message': f"Would move email '{subject}' to '{destination}' (DRY RUN)"
        }
    
    try:
        # Check if destination label exists, create if not
        service = get_gmail_service()
        
        # Get list of all labels
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        # Check if destination label exists
        label_id = None
        for label in labels:
            if label['name'].lower() == destination.lower():
                label_id = label['id']
                break
        
        # Create label if it doesn't exist
        if not label_id:
            label = service.users().labels().create(
                userId='me',
                body={
                    'name': destination,
                    'labelListVisibility': 'labelShow',
                    'messageListVisibility': 'show'
                }
            ).execute()
            label_id = label['id']
        
        # Move message
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={
                'addLabelIds': [label_id],
                'removeLabelIds': ['INBOX']
            }
        ).execute()
        
        # Update labels in database
        session = get_session()
        try:
            email = session.query(Email).filter(Email.id == email_id).first()
            if email:
                labels = email.labels.split(',') if email.labels else []
                
                if 'INBOX' in labels:
                    labels.remove('INBOX')
                
                if label_id not in labels:
                    labels.append(label_id)
                
                email.labels = ','.join(labels)
                session.commit()
        finally:
            session.close()
        
        # Log action
        log_action(email_id, 'move_message', rule_id, 
                  f"Moved email '{subject}' to '{destination}'")
        
        return {
            'success': True,
            'message': f"Moved email to '{destination}'"
        }
    
    except Exception as e:
        # Log error
        log_action(email_id, 'move_message', rule_id, 
                  f"Failed to move email to '{destination}'", 
                  success=False, 
                  error_message=str(e))
        
        return {
            'success': False,
            'message': f"Error: {str(e)}"
        }