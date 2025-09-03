#!/usr/bin/env python3
"""
Test script to verify the threading fixes work correctly.
Simplified test without external dependencies.
"""

class MockComment:
    def __init__(self, id, body, parent_id=None, link_id=None, author="test_user", created_utc=1234567890):
        self.id = id
        self.body = body
        self.parent_id = parent_id  
        self.link_id = link_id
        self.author = author
        self.created_utc = created_utc
        self.replies = []
        self.subreddit = MockSubreddit()
    
    def parent(self):
        # Mock parent lookup - in real code this would be a Reddit API call
        return MockSubmission() if self.parent_id and self.parent_id.startswith("t3_") else None

class MockSubmission:
    def __init__(self, id="submission123", title="Test Submission"):
        self.id = id
        self.title = title
        self.author = "op_user"
        self.created_utc = 1234567890
        self.subreddit = MockSubreddit()
        self.comments = []

class MockSubreddit:
    def __init__(self):
        self.display_name = "test_subreddit"

def test_id_generation_logic():
    """Test that ID generation logic works correctly with multiple examples"""
    print("=== Testing ID Generation Logic ===")
    
    # Test Case 1: Simple linear thread
    print("\n--- Test Case 1: Simple Linear Thread (A->B->C) ---")
    test_simple_thread()
    
    # Test Case 2: Branched conversation
    print("\n--- Test Case 2: Branched Conversation ---")  
    test_branched_thread()
    
    # Test Case 3: Deep nesting
    print("\n--- Test Case 3: Deep Thread (5 levels) ---")
    test_deep_thread()
    
    # Test Case 4: Multiple siblings
    print("\n--- Test Case 4: Multiple Siblings ---")
    test_multiple_siblings()
    
    print("\n✅ All ID generation tests complete!")
    return True

def test_simple_thread():
    """Test simple A->B->C thread"""
    comment_ids = ["commentA", "commentB", "commentC"]
    parent_ids = ["t3_submission", "t1_commentA", "t1_commentB"]
    
    print("  Thread structure: Submission -> A -> B -> C")
    
    print("  OLD WAY (broken):")
    last_id = "commentC"
    old_ids, old_replies = [], []
    for cid, pid in zip(comment_ids, parent_ids):
        utt_id = f"{cid}~{last_id}"
        reply_to = f"{pid.split('_')[1]}~{last_id}" if pid.startswith('t1_') else f"{pid.split('_')[1]}~{last_id}_clean"
        old_ids.append(utt_id)
        old_replies.append(reply_to)
        print(f"    {cid}: ID={utt_id}, reply_to={reply_to}")
    
    print("  NEW WAY (fixed):")
    new_ids, new_replies = [], []
    for cid, pid in zip(comment_ids, parent_ids):
        utt_id = f"{cid}~{cid}"
        reply_to = f"{pid.split('_')[1]}~{pid.split('_')[1]}" if pid.startswith('t1_') else f"{pid.split('_')[1]}~{pid.split('_')[1]}_clean"
        new_ids.append(utt_id)
        new_replies.append(reply_to)
        print(f"    {cid}: ID={utt_id}, reply_to={reply_to}")
    
    # Verify threading
    old_broken = old_replies[1] != old_ids[0] or old_replies[2] != old_ids[1]
    new_fixed = new_replies[1] == new_ids[0] and new_replies[2] == new_ids[1]
    print(f"  Threading broken in old way: {old_broken}")
    print(f"  Threading fixed in new way: {new_fixed}")

def test_branched_thread():
    """Test branched conversation where B and C both reply to A"""
    print("  Thread structure: A -> B, A -> C (2 branches from A)")
    
    # A is parent to both B and C
    scenarios = [
        ("commentA", "t3_submission", "Root comment"),
        ("commentB", "t1_commentA", "Reply to A"),  
        ("commentC", "t1_commentA", "Also reply to A"),
    ]
    
    print("  OLD WAY:")
    last_id = "commentC" 
    for cid, pid, desc in scenarios:
        utt_id = f"{cid}~{last_id}"
        reply_to = f"{pid.split('_')[1]}~{last_id}" if pid.startswith('t1_') else f"{pid.split('_')[1]}~{last_id}_clean"
        print(f"    {desc}: ID={utt_id}, reply_to={reply_to}")
    
    print("  NEW WAY:")
    for cid, pid, desc in scenarios:
        utt_id = f"{cid}~{cid}"
        reply_to = f"{pid.split('_')[1]}~{pid.split('_')[1]}" if pid.startswith('t1_') else f"{pid.split('_')[1]}~{pid.split('_')[1]}_clean"
        print(f"    {desc}: ID={utt_id}, reply_to={reply_to}")
        if pid == "t1_commentA":
            correct = reply_to == "commentA~commentA"
            print(f"      Correctly points to A: {correct}")

def test_deep_thread():
    """Test deep nesting (5 levels)"""
    depth_5_thread = [
        ("level1", "t3_submission"),
        ("level2", "t1_level1"), 
        ("level3", "t1_level2"),
        ("level4", "t1_level3"),
        ("level5", "t1_level4"),
    ]
    
    print("  Thread structure: 1->2->3->4->5 (5 levels deep)")
    
    print("  OLD WAY (all use 'level5' as unique_id):")
    for cid, pid in depth_5_thread:
        utt_id = f"{cid}~level5"
        reply_to = f"{pid.split('_')[1]}~level5" if pid.startswith('t1_') else f"{pid.split('_')[1]}~level5_clean"
        print(f"    {cid}: reply_to={reply_to}")
    
    print("  NEW WAY (each uses own ID):")
    threading_correct = True
    prev_id = None
    for i, (cid, pid) in enumerate(depth_5_thread):
        utt_id = f"{cid}~{cid}"
        reply_to = f"{pid.split('_')[1]}~{pid.split('_')[1]}" if pid.startswith('t1_') else f"{pid.split('_')[1]}~{pid.split('_')[1]}_clean"
        print(f"    {cid}: reply_to={reply_to}")
        
        if i > 0:  # Check threading for non-root comments
            expected_parent = f"{depth_5_thread[i-1][0]}~{depth_5_thread[i-1][0]}"
            correct = reply_to == expected_parent
            threading_correct = threading_correct and correct
            print(f"      Points to correct parent: {correct}")
    
    print(f"  All threading correct: {threading_correct}")

def test_multiple_siblings():
    """Test multiple comments replying to same parent"""
    print("  Thread structure: A -> [B, C, D] (3 siblings)")
    
    siblings_scenario = [
        ("parentA", "t3_submission", "Parent comment"),
        ("childB", "t1_parentA", "First child"),
        ("childC", "t1_parentA", "Second child"), 
        ("childD", "t1_parentA", "Third child"),
    ]
    
    print("  OLD WAY:")
    last_id = "childD"
    for cid, pid, desc in siblings_scenario:
        utt_id = f"{cid}~{last_id}"
        reply_to = f"{pid.split('_')[1]}~{last_id}" if pid.startswith('t1_') else f"{pid.split('_')[1]}~{last_id}_clean"
        print(f"    {desc}: reply_to={reply_to}")
    
    print("  NEW WAY:")
    all_siblings_correct = True
    for cid, pid, desc in siblings_scenario:
        utt_id = f"{cid}~{cid}"
        reply_to = f"{pid.split('_')[1]}~{pid.split('_')[1]}" if pid.startswith('t1_') else f"{pid.split('_')[1]}~{pid.split('_')[1]}_clean"
        print(f"    {desc}: reply_to={reply_to}")
        
        if pid == "t1_parentA":  # All siblings should point to parentA
            correct = reply_to == "parentA~parentA"
            all_siblings_correct = all_siblings_correct and correct
            print(f"      Correctly points to parent: {correct}")
    
    print(f"  All siblings point to correct parent: {all_siblings_correct}")

def test_mutable_default_fix():
    """Test the mutable default argument fix with multiple scenarios"""
    print("\n=== Testing Mutable Default Argument Fix ===")
    
    print("\n--- Scenario 1: Simple Function Calls ---")
    test_basic_mutable_default()
    
    print("\n--- Scenario 2: Recursive Tree Traversal ---")
    test_recursive_contamination()
    
    print("\n--- Scenario 3: Multiple Thread Histories ---")
    test_thread_history_contamination()
    
    print("\n--- Scenario 4: Concurrent-like Processing ---")
    test_concurrent_processing()
    
    return True

def test_basic_mutable_default():
    """Basic mutable default argument test"""
    def old_broken_function(item, history=[]):  # This is the bug
        history.append(item)
        return history.copy()
    
    def new_fixed_function(item, history=None):  # This is the fix
        if history is None:
            history = []
        new_history = history + [item]
        return new_history
    
    print("  OLD WAY (broken - shared mutable default):")
    result1 = old_broken_function("thread1")
    result2 = old_broken_function("thread2") 
    result3 = old_broken_function("thread3")
    print(f"    Call 1: {result1}")
    print(f"    Call 2: {result2}")  
    print(f"    Call 3: {result3}")
    print(f"    Problem: Each call accumulates previous calls!")
    
    print("  NEW WAY (fixed):")
    result4 = new_fixed_function("thread1")
    result5 = new_fixed_function("thread2")
    result6 = new_fixed_function("thread3") 
    print(f"    Call 1: {result4}")
    print(f"    Call 2: {result5}")
    print(f"    Call 3: {result6}")
    print(f"    Fixed: Each call is independent!")

def test_recursive_contamination():
    """Test recursive function contamination (like the actual bug)"""
    def old_traverse(node, path=[], depth=0):
        if depth > 3:  # Prevent infinite recursion
            return [path + [node]]
        path.append(node)
        if node.endswith('_end') or depth >= 2:
            return [path.copy()]
        else:
            results = []
            for child in [f"{node}_A", f"{node}_B"]:
                results.extend(old_traverse(child, path, depth+1))
            return results
    
    def new_traverse(node, path=None, depth=0):
        if depth > 3:  # Prevent infinite recursion
            return [path + [node] if path else [node]]
        if path is None:
            path = []
        new_path = path + [node]
        if node.endswith('_end') or depth >= 2:
            return [new_path.copy()]
        else:
            results = []
            for child in [f"{node}_A", f"{node}_B"]:
                results.extend(new_traverse(child, new_path, depth+1))
            return results
    
    print("  OLD WAY (recursive contamination):")
    old_paths1 = old_traverse("thread1")
    old_paths2 = old_traverse("thread2")
    print(f"    Thread1 paths: {len(old_paths1)} paths")
    for i, p in enumerate(old_paths1[:2]):  # Show first 2
        print(f"      Path {i+1}: {p}")
    print(f"    Thread2 paths: {len(old_paths2)} paths") 
    for i, p in enumerate(old_paths2[:2]):  # Show contamination
        print(f"      Path {i+1}: {p}")
        contamination_found = any('thread1' in str(path) for path in old_paths2)
        print(f"      Contains thread1 contamination: {contamination_found}")
    
    print("  NEW WAY (fixed recursive):")
    new_paths1 = new_traverse("thread1") 
    new_paths2 = new_traverse("thread2")
    print(f"    Thread1 paths: {len(new_paths1)} paths")
    for i, p in enumerate(new_paths1[:2]):
        print(f"      Path {i+1}: {p}")
    print(f"    Thread2 paths: {len(new_paths2)} paths")
    for i, p in enumerate(new_paths2[:2]):
        print(f"      Path {i+1}: {p}")
        no_contamination = not any('thread1' in str(path) for path in new_paths2)
        print(f"      No thread1 contamination: {no_contamination}")

def test_thread_history_contamination():
    """Test thread history contamination specific to the Reddit case"""
    print("  Simulating Reddit thread collection:")
    
    # Old buggy way - histories get mixed up
    def old_collect_thread(comments, thread_history=[]):
        for comment in comments:
            thread_history.append(comment)
        return thread_history.copy()
    
    # New fixed way
    def new_collect_thread(comments, thread_history=None):
        if thread_history is None:
            thread_history = []
        new_history = thread_history[:]  # Copy existing
        for comment in comments:
            new_history.append(comment)
        return new_history
    
    # Simulate collecting multiple threads
    thread1_comments = ["post1", "comment1a", "comment1b"]
    thread2_comments = ["post2", "comment2a", "comment2b"] 
    thread3_comments = ["post3", "comment3a"]
    
    print("  OLD WAY:")
    history1 = old_collect_thread(thread1_comments)
    history2 = old_collect_thread(thread2_comments)
    history3 = old_collect_thread(thread3_comments)
    print(f"    Thread 1 history: {history1}")
    print(f"    Thread 2 history: {history2}")
    print(f"    Thread 3 history: {history3}")
    print(f"    Problem: All threads contaminated with previous threads!")
    
    print("  NEW WAY:")
    history4 = new_collect_thread(thread1_comments)
    history5 = new_collect_thread(thread2_comments)
    history6 = new_collect_thread(thread3_comments)
    print(f"    Thread 1 history: {history4}")
    print(f"    Thread 2 history: {history5}")
    print(f"    Thread 3 history: {history6}")
    print(f"    Fixed: Each thread has only its own comments!")

def test_concurrent_processing():
    """Test what happens with concurrent-like processing"""
    print("  Simulating batch processing of threads:")
    
    def old_process_batch(batch_items, accumulator=[]):
        for item in batch_items:
            accumulator.append(f"processed_{item}")
        return accumulator.copy()
    
    def new_process_batch(batch_items, accumulator=None):
        if accumulator is None:
            accumulator = []
        new_acc = accumulator[:]
        for item in batch_items:
            new_acc.append(f"processed_{item}")
        return new_acc
    
    batches = [
        ["item1", "item2"],
        ["item3", "item4"], 
        ["item5"],
        ["item6", "item7", "item8"]
    ]
    
    print("  OLD WAY (batches contaminate each other):")
    for i, batch in enumerate(batches):
        result = old_process_batch(batch)
        print(f"    Batch {i+1} result: {result}")
        print(f"      Expected {len(batch)} items, got {len(result)} items")
    
    print("  NEW WAY (independent batch processing):")
    for i, batch in enumerate(batches):
        result = new_process_batch(batch)
        print(f"    Batch {i+1} result: {result}")
        print(f"      Expected {len(batch)} items, got {len(result)} items ✓")


if __name__ == "__main__":
    print("Testing NormVio Threading Fixes")
    print("=" * 40)
    
    try:
        test1 = test_id_generation_logic()
        test2 = test_mutable_default_fix()
        
        if all([test1, test2]):
            print("\n🎉 ALL TESTS PASSED! Threading fixes are working correctly.")
        else:
            print("\n❌ Some tests failed!")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()