#!/usr/bin/env python3
"""
Utility script to process deleted comment logs and attempt restoration 
using alternative data sources when available.

Usage:
    python src/restore_deleted_comments.py <log_file_path> [--output output_file]
"""

import sys
import os
import json
import argparse
from datetime import datetime
from collections import defaultdict

def parse_deleted_comment_log(log_file):
    """Parse the deleted comment log file"""
    deleted_comments = []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse format: timestamp | kind: id | subreddit: name | context: info
                    parts = line.split(' | ')
                    if len(parts) < 3:
                        print(f"Warning: Malformed line {line_num}: {line}")
                        continue
                    
                    timestamp_str = parts[0]
                    kind_id = parts[1]
                    subreddit_part = parts[2]
                    context = parts[3] if len(parts) > 3 else ""
                    
                    # Extract kind and id
                    if ': ' in kind_id:
                        kind, comment_id = kind_id.split(': ', 1)
                    else:
                        print(f"Warning: Could not parse kind:id from line {line_num}")
                        continue
                    
                    # Extract subreddit
                    if subreddit_part.startswith('subreddit: '):
                        subreddit = subreddit_part.replace('subreddit: ', '')
                    else:
                        subreddit = "unknown"
                    
                    deleted_comments.append({
                        'timestamp': timestamp_str,
                        'kind': kind,
                        'id': comment_id,
                        'subreddit': subreddit,
                        'context': context,
                        'line_number': line_num
                    })
                    
                except Exception as e:
                    print(f"Error parsing line {line_num}: {e}")
                    continue
                    
    except FileNotFoundError:
        print(f"Error: Log file not found: {log_file}")
        return []
    except Exception as e:
        print(f"Error reading log file: {e}")
        return []
    
    return deleted_comments

def analyze_deleted_comments(deleted_comments):
    """Analyze patterns in deleted comments"""
    analysis = {
        'total_deleted': len(deleted_comments),
        'by_subreddit': defaultdict(int),
        'by_kind': defaultdict(int),
        'by_reason': defaultdict(int),
        'unique_ids': set()
    }
    
    for comment in deleted_comments:
        analysis['by_subreddit'][comment['subreddit']] += 1
        analysis['by_kind'][comment['kind']] += 1
        analysis['unique_ids'].add(comment['id'])
        
        # Analyze deletion reasons from context
        context = comment['context'].lower()
        if '[removed]' in context:
            analysis['by_reason']['moderator_removed'] += 1
        elif '[deleted]' in context:
            analysis['by_reason']['user_deleted'] += 1
        elif 'fetch_error' in context:
            analysis['by_reason']['fetch_failed'] += 1
        else:
            analysis['by_reason']['other'] += 1
    
    analysis['unique_comment_count'] = len(analysis['unique_ids'])
    return analysis

def export_for_restoration(deleted_comments, output_file):
    """Export deleted comment IDs in format suitable for restoration tools"""
    
    # Group by subreddit for efficient restoration
    by_subreddit = defaultdict(list)
    for comment in deleted_comments:
        by_subreddit[comment['subreddit']].append({
            'id': comment['id'],
            'kind': comment['kind'],
            'timestamp': comment['timestamp'],
            'context': comment['context']
        })
    
    export_data = {
        'export_timestamp': datetime.now().isoformat(),
        'total_deleted_comments': len(deleted_comments),
        'unique_comments': len(set(c['id'] for c in deleted_comments)),
        'subreddits': dict(by_subreddit)
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(deleted_comments)} deleted comments to {output_file}")
    return export_data

def main():
    parser = argparse.ArgumentParser(description='Process deleted comment logs')
    parser.add_argument('log_file', help='Path to deleted comment log file')
    parser.add_argument('--output', '-o', help='Output file for restoration data (JSON)')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze, don\'t export')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.log_file):
        print(f"Error: Log file does not exist: {args.log_file}")
        return 1
    
    print(f"Processing deleted comment log: {args.log_file}")
    deleted_comments = parse_deleted_comment_log(args.log_file)
    
    if not deleted_comments:
        print("No deleted comments found in log file.")
        return 0
    
    print(f"\nParsed {len(deleted_comments)} deleted comment entries")
    
    # Analyze the deleted comments
    analysis = analyze_deleted_comments(deleted_comments)
    
    print("\n=== DELETED COMMENT ANALYSIS ===")
    print(f"Total entries: {analysis['total_deleted']}")
    print(f"Unique comment IDs: {analysis['unique_comment_count']}")
    print(f"\nBy subreddit:")
    for subreddit, count in sorted(analysis['by_subreddit'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {subreddit}: {count}")
    
    print(f"\nBy content type:")
    for kind, count in analysis['by_kind'].items():
        print(f"  {kind}: {count}")
    
    print(f"\nBy deletion reason:")
    for reason, count in analysis['by_reason'].items():
        print(f"  {reason}: {count}")
    
    if not args.analyze_only:
        # Export for restoration
        if args.output:
            output_file = args.output
        else:
            base_name = os.path.splitext(os.path.basename(args.log_file))[0]
            output_file = f"deleted_comments_export_{base_name}.json"
        
        export_for_restoration(deleted_comments, output_file)
        print(f"\n💾 Restoration data saved to: {output_file}")
        print("This file can be used with future restoration tools when alternative APIs become available.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())