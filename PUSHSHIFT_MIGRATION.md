# Pushshift API Migration

## Background
The Pushshift API, which was used to fetch deleted/removed Reddit content, is no longer accessible as of 2023. This document outlines the changes made to migrate from Pushshift to PRAW-only implementation.

## Changes Made

### 1. Removed Dependencies
- **psaw** package removed from requirements.txt
- All Pushshift imports removed from scraper.py

### 2. Updated Functions

#### `scraper.py`
- **`__init__`**: Removed PushshiftAPI initialization
- **`get_comments`**: Now uses PRAW-only comment fetching
- **`fetch_psaw_from_id`**: Replaced with PRAW equivalent (cannot recover deleted content)
- **`fetch_psaw_from_ids`**: Replaced with PRAW batch fetching (cannot recover deleted content)

### 3. Functional Limitations

**IMPORTANT**: The new implementation has significant limitations:

#### What Still Works:
- ✅ Fetching moderator comments (if not deleted)
- ✅ Getting community rules
- ✅ Collecting thread context (non-deleted comments)
- ✅ Basic data pipeline functionality

#### What No Longer Works:
- ❌ **Cannot recover deleted/removed comments** (core dataset limitation)
- ❌ Cannot fetch comment history beyond PRAW's limits
- ❌ Cannot access comments older than ~1000 recent comments per user

### 4. Impact on Data Collection

#### Moderate Impact:
- **get_mod_comments.py**: Still works but misses deleted mod comments
- **get_thread_and_deleted_comment.py**: Cannot restore deleted parent comments

#### Critical Impact:
- **Dataset quality**: Significantly reduced as deleted comments were key data points
- **Thread reconstruction**: Many threads will be incomplete without deleted content

### 5. Alternative Solutions

Since the dataset fundamentally relies on deleted content analysis, consider:

1. **Use existing datasets**: Pre-collected data with Pushshift content
2. **Manual moderation logs**: Direct access to subreddit moderation logs
3. **Real-time collection**: Monitor subreddits before content gets deleted
4. **Third-party archives**: Other archived Reddit data sources

### 6. Updated Pipeline Behavior

The pipeline will now:
- Skip comments it cannot fetch (instead of restoring them)
- Have lower success rates for thread reconstruction  
- Miss the core "moderated vs clean" distinction that relies on deleted content

### 7. Configuration Required

Update your `config.py` with valid Reddit API credentials:
```python
PRAW_CLIENT_ID = 'your_client_id'
PRAW_CLIENT_SECRET = 'your_client_secret' 
PRAW_USERNAME = 'your_username'
PRAW_PW = 'your_password'
```

## Recommendation

Given the fundamental reliance on deleted content, **consider using pre-existing datasets** collected when Pushshift was available, rather than running the collection pipeline with these limitations.