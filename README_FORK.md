# RedditMod - Enhanced NormVio Fork

This fork addresses critical issues in the original NormVio dataset collection pipeline and adds significant improvements.

## 🚀 Key Improvements

### ✅ Fixed Critical Bugs
- **Threading Bug**: Fixed non-linear parent-child relationships in clean threads
- **Mutable Default**: Fixed list contamination in recursive thread traversal  
- **Dictionary Access**: Fixed alpha_val key lookup bug
- **Shell Execution**: Fixed incorrect python script execution

### 🔄 Pushshift Migration
- **Complete removal** of deprecated Pushshift API dependency
- **PRAW-only implementation** with comprehensive error handling
- **Deleted content tracking** for future restoration possibilities
- **Hybrid subreddit collection** (PRAW + web scraping fallback)

### 📊 Enhanced Data Quality
- **Separate logging** for moderated vs user-deleted content
- **Better error handling** throughout the pipeline
- **Comprehensive statistics** and progress reporting
- **Validation tools** for data integrity

## 🛠 New Tools

- `src/get_top_subreddits_praw.py`: Enhanced subreddit collection
- `src/restore_deleted_comments.py`: Deleted comment analysis and export
- `test_threading_fix.py`: Comprehensive test suite for fixes
- `PUSHSHIFT_MIGRATION.md`: Detailed migration documentation

## 📈 Impact

- **Maintains functionality** without deprecated APIs
- **Significantly improved** thread reconstruction accuracy  
- **Better data preservation** for future restoration
- **Enhanced reliability** and error recovery

## 🔧 Usage

Same as original NormVio, but with:
- More reliable data collection
- Better error reporting
- Comprehensive logging of missing data
- Future-proofed architecture

See `PUSHSHIFT_MIGRATION.md` for detailed changes and limitations.

---

**Original NormVio**: Research dataset for norm violation detection  
**This Fork**: Production-ready version with critical fixes and improvements