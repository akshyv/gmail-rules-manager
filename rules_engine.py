"""
Rules engine for Gmail Rules Manager
"""

import json
import re
from datetime import datetime, timedelta
from db import get_session, Email, get_email_by_id

class RulesEngine:
    """Rules engine for processing emails based on defined rules"""
    
    def __init__(self, rules_file):
        """
        Initialize rules engine.
        
        Args:
            rules_file (str): Path to the JSON file containing rules
        """
        self.rules_file = rules_file
        self.rules = self._load_rules()
    
    def _load_rules(self):
        """
        Load rules from JSON file.
        
        Returns:
            list: List of rule dictionaries
        """
        with open(self.rules_file, 'r') as f:
            data = json.load(f)
        return data['rules']
    
    def evaluate_emails(self, email_ids=None):
        """
        Evaluate rules against emails in the database.
        
        Args:
            email_ids (list): List of email IDs to evaluate. 
                             If None, all emails will be evaluated.
                             
        Returns:
            dict: Dictionary mapping email IDs to applicable actions
        """
        session = get_session()
        results = {}
        
        try:
            # Query for emails
            query = session.query(Email)
            if email_ids:
                query = query.filter(Email.id.in_(email_ids))
            
            emails = query.all()
            
            # Store necessary data to avoid session issues
            email_data = []
            for email in emails:
                email_data.append({
                    'id': email.id,
                    'email': email
                })
            
        finally:
            session.close()
        
        # Process rules outside of the session
        for data in email_data:
            email_id = data['id']
            email = data['email']
            applicable_actions = []
            
            # Check each rule
            for rule in self.rules:
                if self._rule_applies(rule, email):
                    # Rule applies, add its actions to the list
                    for action in rule['actions']:
                        applicable_actions.append({
                            'action': action,
                            'rule_id': rule['id']
                        })
            
            if applicable_actions:
                results[email_id] = applicable_actions
        
        return results
    
    def _rule_applies(self, rule, email):
        """
        Check if a rule applies to an email.
        
        Args:
            rule (dict): Rule dictionary
            email (Email): Email object
            
        Returns:
            bool: True if rule applies, False otherwise
        """
        conditions = rule['conditions']
        predicate = rule['predicate']
        
        # Handle different predicates
        if predicate == 'all':
            # All conditions must match
            return all(self._condition_matches(condition, email) for condition in conditions)
        elif predicate == 'any':
            # At least one condition must match
            return any(self._condition_matches(condition, email) for condition in conditions)
        else:
            raise ValueError(f"Unknown predicate: {predicate}")
    
    def _condition_matches(self, condition, email):
        """
        Check if a condition matches an email.
        
        Args:
            condition (dict): Condition dictionary
            email (Email): Email object
            
        Returns:
            bool: True if condition matches, False otherwise
        """
        field = condition['field'].lower()
        predicate = condition['predicate'].lower()
        value = condition['value']
        
        # Get field value from email
        if field == 'from':
            field_value = email.from_address
        elif field == 'to':
            field_value = email.to_address
        elif field == 'subject':
            field_value = email.subject
        elif field == 'message':
            field_value = email.body_text or ""
        elif field == 'received_date':
            return self._check_date_condition(predicate, value, condition.get('unit', 'days'), email.received_date)
        else:
            raise ValueError(f"Unknown field: {field}")
        
        # Check string conditions
        if predicate == 'contains':
            return value.lower() in field_value.lower()
        elif predicate == 'does_not_contain':
            return value.lower() not in field_value.lower()
        elif predicate == 'equals':
            return value.lower() == field_value.lower()
        elif predicate == 'does_not_equal':
            return value.lower() != field_value.lower()
        else:
            raise ValueError(f"Unknown predicate: {predicate}")
    
    def _check_date_condition(self, predicate, value, unit, email_date):
        """
        Check a date condition.
        
        Args:
            predicate (str): Predicate type ('less_than' or 'greater_than')
            value (str): Value to compare with (e.g., '7')
            unit (str): Unit of time ('days' or 'months')
            email_date (datetime): The email's received date
            
        Returns:
            bool: True if condition matches, False otherwise
        """
        if not email_date:
            return False
        
        try:
            value = int(value)
        except ValueError:
            return False
        
        now = datetime.utcnow()
        
        # Calculate time difference
        if unit == 'days':
            time_diff = (now - email_date).days
        elif unit == 'months':
            # Approximate months as 30 days for simplicity
            time_diff = (now - email_date).days // 30
        else:
            raise ValueError(f"Unknown unit: {unit}")
        
        # Check the condition
        if predicate == 'less_than':
            return time_diff < value
        elif predicate == 'greater_than':
            return time_diff > value
        else:
            raise ValueError(f"Unknown date predicate: {predicate}")