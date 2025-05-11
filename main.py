"""
Main script for Gmail Rules Manager
"""

import argparse
import sys
import json
from db import init_db
from email_fetcher import fetch_emails
from rules_engine import RulesEngine
from actions import execute_actions
from config import RULES_FILE, DRY_RUN

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Gmail Rules Manager')
    
    parser.add_argument('--fetch', action='store_true',
                        help='Fetch emails from Gmail')
    
    parser.add_argument('--process', action='store_true',
                        help='Process emails with rules')
    
    parser.add_argument('--limit', type=int, default=20,
                        help='Maximum number of emails to fetch (default: 20)')
    
    parser.add_argument('--dry-run', action='store_true',
                        help='Do not actually perform actions, just simulate')
    
    parser.add_argument('--rules-file', type=str, default=RULES_FILE,
                        help=f'Path to rules JSON file (default: {RULES_FILE})')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    
    # Initialize database
    init_db()
    
    # Fetch emails if requested
    email_ids = None
    if args.fetch:
        print(f"Fetching up to {args.limit} emails from Gmail...")
        email_ids = fetch_emails(limit=args.limit)
        print(f"Fetched {len(email_ids)} emails.")
    
    # Process emails if requested
    if args.process:
        # Create rules engine
        rules_engine = RulesEngine(args.rules_file)
        
        print(f"Processing emails with rules from {args.rules_file}...")
        
        # Evaluate rules against emails
        applicable_actions = rules_engine.evaluate_emails(email_ids)
        
        if not applicable_actions:
            print("No actions to perform.")
            return
        
        # Print applicable actions in verbose mode
        if args.verbose:
            print("\nApplicable actions:")
            for email_id, actions in applicable_actions.items():
                print(f"Email ID {email_id}:")
                for action_info in actions:
                    action = action_info['action']
                    rule_id = action_info['rule_id']
                    print(f"  - Rule {rule_id}: {action['type']}")
        
        # Ask for confirmation
        response = input(f"\nFound {len(applicable_actions)} emails with applicable actions. Proceed? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
        
        # Execute actions
        print("Executing actions...")
        results = execute_actions(applicable_actions)
        
        # Print results
        print("\nResults:")
        for email_id, action_results in results.items():
            for result in action_results:
                status = "✓" if result['success'] else "✗"
                print(f"{status} {result['message']}")
        
        # Print summary
        total = sum(len(actions) for actions in results.values())
        success = sum(1 for action_results in results.values() 
                     for result in action_results if result['success'])
        print(f"\nSummary: {success}/{total} actions completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)