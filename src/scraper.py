import sys
import time
import os
import praw
from datetime import datetime
from tqdm import tqdm
from config import PRAW_CLIENT_ID, PRAW_CLIENT_SECRET, PRAW_USERNAME, PRAW_PW

def wrap_error_with_blank(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except:
            result = []
            print("Error with function - ", func, " with args ", args, kwargs)
        return result

    return wrapper

class RedditScraper:
    def __init__(self):
        if PRAW_CLIENT_ID and PRAW_CLIENT_SECRET and PRAW_USERNAME and PRAW_PW:
            try:
                self.r = praw.Reddit(client_id=PRAW_CLIENT_ID, client_secret=PRAW_CLIENT_SECRET,
                                    user_agent='Get Comments', username=PRAW_USERNAME, password=PRAW_PW)
                if self.r.user.me() is None:
                    print("Reddit API Authentication failed")
                    self.r = None
                else:
                    print(f"Authenticated as: {self.r.user.me()}")
            except Exception as e:
                print(f"Reddit API Authentication failed: {e}")
                self.r = None
        else:
            print("Reddit API credentials not found in config.py")
            self.r = None
        
        # Initialize deleted comment tracking
        self.deleted_comments_dir = "data/deleted_comments/"
        if not os.path.exists(self.deleted_comments_dir):
            os.makedirs(self.deleted_comments_dir)
        
        self.deleted_comment_log = os.path.join(self.deleted_comments_dir, f"deleted_comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        self.moderated_only_log = os.path.join(self.deleted_comments_dir, f"moderated_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        self.deleted_count = 0
        self.moderated_count = 0

    @wrap_error_with_blank
    def get_moderators(self, subreddit):
        try:
            moderators = [moderator for moderator in self.r.subreddit(
                subreddit).moderator()]
        except:
            time.sleep(10)
            try:
                moderators = [moderator for moderator in self.r.subreddit(
                    subreddit).moderator()]
            except:
                moderators = []
                print("Error with r/", subreddit)
        return moderators
    
    @wrap_error_with_blank
    def get_mod_comments(self, mods, subreddit, limit=100):
        mod_comments = []
        for mod in tqdm(mods, leave=False):
            _mod_comments = self.get_comments(mod, limit=limit, subreddit=subreddit)
            mod_comments += [_mod_comments]
        # mod_comments = [self.get_comments(
        #     mod, limit=limit, subreddit=subreddit) for mod in mods]
        mod_comments = [[comment for comment in thread] for thread in mod_comments]
        return mod_comments

    @wrap_error_with_blank
    def get_comments(self, user, limit=100, subreddit=None):
        try:
            # Use PRAW only - get user's recent comments
            comments = [comment for comment in user.comments.new(limit=limit)]
            if subreddit is not None:
                # Filter by subreddit if specified
                comments = [comment for comment in comments if comment.subreddit.display_name == subreddit]
        except Exception as e:
            comments = []
            print(f"Error getting comments for u/{getattr(user, 'name', user)}: {e}")
        return comments

    @wrap_error_with_blank
    def get_community_rules(self, subreddit):
            try:
                rules = [rule for rule in self.r.subreddit(subreddit).rules]
            except:
                rules = None
                print("Rule Scraping Error with ", subreddit)
            return rules
    
    @wrap_error_with_blank
    def get_submissions(self, subreddit, limit=100, time_filter='month'):
        return [x for x in self.r.subreddit(subreddit).top(limit=limit, time_filter=time_filter)]

    def log_deleted_comment(self, comment_id, subreddit, kind="comment", context=None, deletion_type="unknown"):
        """Log deleted comment details for potential future restoration"""
        try:
            timestamp = datetime.now().isoformat()
            context_info = f" | context: {context}" if context else ""
            log_line = f"{timestamp} | {kind}: {comment_id} | subreddit: {subreddit} | type: {deletion_type}{context_info}\n"
            
            # Log to main file (all deleted content)
            with open(self.deleted_comment_log, 'a', encoding='utf-8') as f:
                f.write(log_line)
            self.deleted_count += 1
            
            # Also log to moderated-only file if it's moderator-removed
            if deletion_type == "moderator_removed":
                with open(self.moderated_only_log, 'a', encoding='utf-8') as f:
                    f.write(log_line)
                self.moderated_count += 1
                
        except Exception as e:
            print(f"Error logging deleted comment: {e}")

    def fetch_psaw_from_id(self, id_to_be_fetched, subreddit, kind="comment"):
        """
        PRAW-only replacement for pushshift fetch.
        Note: This cannot recover deleted/removed content like pushshift could.
        Logs deleted content for potential future restoration.
        """
        try:
            if kind == "comment":
                # Try to fetch comment via PRAW
                comment = self.r.comment(id_to_be_fetched)
                comment.refresh()  # Load the comment data
                if comment.body == '[removed]':
                    # Log moderator-removed comment
                    self.log_deleted_comment(id_to_be_fetched, subreddit, kind, f"body: {comment.body}", "moderator_removed")
                    return None
                elif comment.body == '[deleted]':
                    # Log user-deleted comment
                    self.log_deleted_comment(id_to_be_fetched, subreddit, kind, f"body: {comment.body}", "user_deleted")
                    return None
                return comment
            elif kind == "submission":
                submission = self.r.submission(id_to_be_fetched)
                if submission.selftext == '[removed]':
                    # Log moderator-removed submission
                    self.log_deleted_comment(id_to_be_fetched, subreddit, kind, f"selftext: {submission.selftext}", "moderator_removed")
                    return None
                elif submission.selftext == '[deleted]':
                    # Log user-deleted submission
                    self.log_deleted_comment(id_to_be_fetched, subreddit, kind, f"selftext: {submission.selftext}", "user_deleted")
                    return None
                return submission
        except Exception as e:
            # Log failed fetch attempts (likely deleted/removed content)
            self.log_deleted_comment(id_to_be_fetched, subreddit, kind, f"fetch_error: {str(e)}", "fetch_failed")
            print(f"Could not fetch {kind} {id_to_be_fetched}: {e}")
        return None

    def fetch_psaw_from_ids(self, ids_to_be_fetched, subreddit=None, kind="comment"):
        """
        PRAW-only replacement for pushshift batch fetch.
        Note: This cannot recover deleted/removed content like pushshift could.
        Logs all deleted content for potential future restoration.
        """
        fetched = {}
        deleted_count_before = self.deleted_count
        
        for comment_id in tqdm(ids_to_be_fetched, desc=f"Fetching {kind}s", leave=False):
            result = self.fetch_psaw_from_id(comment_id, subreddit, kind)
            if result is not None:
                fetched[comment_id] = result
            time.sleep(0.1)  # Rate limiting
        
        deleted_count_this_batch = self.deleted_count - deleted_count_before
        if deleted_count_this_batch > 0:
            print(f"Logged {deleted_count_this_batch} deleted {kind}s to {self.deleted_comment_log}")
        
        return fetched

    def get_deleted_comment_summary(self):
        """Get summary of deleted comments logged during this session"""
        return {
            "total_deleted": self.deleted_count,
            "moderated_only": self.moderated_count,
            "user_deleted": self.deleted_count - self.moderated_count,
            "log_file": self.deleted_comment_log,
            "moderated_log_file": self.moderated_only_log,
            "log_exists": os.path.exists(self.deleted_comment_log),
            "moderated_log_exists": os.path.exists(self.moderated_only_log)
        }