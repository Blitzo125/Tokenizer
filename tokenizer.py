# ============================================================================
# HIGHLY OPTIMIZED TOKENIZER - CONFIGURATION
# ============================================================================
INPUT_FILE = 'input.txt'
CHARS_TO_READ = 50000  # Set to None to read ALL characters
ENCODING = 'utf-8'
NUM_MERGES = 500
START_TOKEN_IDX = 256
SHOW_TOP_PAIRS = 10
SHOW_PROGRESS = False
# ============================================================================

from collections import Counter
import json
import time

def read_text_from_file(filename, num_chars=None, encoding='utf-8'):
    """Read file content efficiently."""
    with open(filename, 'r', encoding=encoding) as file:
        return file.read() if num_chars is None else file.read(num_chars)

def text_to_tokens(text):
    """Convert text to tokens efficiently."""
    return list(text.encode('utf-8'))

def find_token_pairs(tokens):
    """Find token pairs using list comprehension for speed."""
    return [tuple(tokens[i:i+2]) for i in range(len(tokens) - 1)]

def count_pair_frequencies(token_pairs):
    """Count frequencies using Counter."""
    return Counter(token_pairs)

def get_most_frequent_pairs(pair_counts, num_pairs):
    """Get most frequent pairs."""
    return pair_counts.most_common(num_pairs)

def merge(ids, pair, idx):
    """Optimized merge function with early exit."""
    if len(ids) < 2:
        return ids
    
    newids = []
    i = 0
    while i < len(ids):
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i+1] == pair[1]:
            newids.append(idx)
            i += 2
        else:
            newids.append(ids[i])
            i += 1
    return newids

def perform_merges(tokens, num_merges, start_token_idx, show_progress=True):
    """Perform merges with progress tracking and early stopping."""
    current_tokens = tokens.copy()
    next_token_idx = start_token_idx
    merge_rules = []
    start_time = time.time()
    
    for merge_iteration in range(num_merges):
        # Find most frequent pairs efficiently
        token_pairs = find_token_pairs(current_tokens)
        if not token_pairs:  # Early exit if no pairs left
            break
            
        pair_counts = count_pair_frequencies(token_pairs)
        most_common_pair = pair_counts.most_common(1)[0]
        
        # Skip if pair only appears once (no benefit)
        if most_common_pair[1] < 2:
            break
        
        if show_progress and merge_iteration % 50 == 0:  # Show progress every 50 iterations
            elapsed = time.time() - start_time
            print(f"Merge {merge_iteration + 1}/{num_merges} - Pair: {most_common_pair[0]} (count: {most_common_pair[1]}) - Time: {elapsed:.2f}s")
        
        # Store merge rule
        merge_rules.append({
            'pair': most_common_pair[0],
            'new_token': next_token_idx,
            'count': most_common_pair[1]
        })
        
        # Apply merge
        current_tokens = merge(current_tokens, most_common_pair[0], next_token_idx)
        next_token_idx += 1
        
        # Early stopping if no more merges possible
        if len(current_tokens) <= 1:
            break
    
    total_time = time.time() - start_time
    if show_progress:
        print(f"Completed {len(merge_rules)} merges in {total_time:.2f} seconds")
    
    return current_tokens, next_token_idx, merge_rules

def encode_text(text, merge_rules, start_token_idx=256):
    """Encode text efficiently."""
    tokens = text_to_tokens(text)
    
    for rule in merge_rules:
        tokens = merge(tokens, rule['pair'], rule['new_token'])
    
    return tokens

def decode_text(tokens, merge_rules, start_token_idx=256):
    """Decode tokens efficiently."""
    current_tokens = tokens.copy()
    
    for rule in reversed(merge_rules):
        new_tokens = []
        i = 0
        while i < len(current_tokens):
            if current_tokens[i] == rule['new_token']:
                new_tokens.extend(rule['pair'])
                i += 1
            else:
                new_tokens.append(current_tokens[i])
                i += 1
        current_tokens = new_tokens
    
    try:
        return bytes(current_tokens).decode('utf-8')
    except UnicodeDecodeError:
        return f"[Decoding failed. Tokens: {current_tokens}]"

def save_merge_rules(merge_rules, filename='merge_rules.json'):
    """Save merge rules efficiently."""
    with open(filename, 'w') as f:
        json.dump(merge_rules, f, indent=2)
    print(f"Merge rules saved to {filename} ({len(merge_rules)} rules)")

def load_merge_rules(filename='merge_rules.json'):
    """Load merge rules efficiently."""
    with open(filename, 'r') as f:
        return json.load(f)

def print_summary(original_tokens, final_tokens, next_token_idx, start_token_idx, show_top_pairs):
    """Print optimized summary."""
    print(f"\n=== OPTIMIZATION SUMMARY ===")
    print(f"Original tokens: {len(original_tokens)}")
    print(f"Final tokens: {len(final_tokens)}")
    print(f"Compression: {((len(original_tokens) - len(final_tokens)) / len(original_tokens) * 100):.1f}%")
    print(f"Vocabulary size: {next_token_idx - start_token_idx} new tokens")
    
    # Show top pairs efficiently
    if show_top_pairs > 0:
        final_pairs = find_token_pairs(final_tokens)
        final_counts = count_pair_frequencies(final_pairs)
        top_pairs = get_most_frequent_pairs(final_counts, show_top_pairs)
        
        print(f"\nTop {show_top_pairs} remaining pairs:")
        for i, (pair, count) in enumerate(top_pairs, 1):
            print(f"{i:2d}. {pair} - {count}")

def main():
    """Optimized main function."""
    print("=== HIGHLY OPTIMIZED TOKENIZER ===")
    start_time = time.time()
    
    # Read and tokenize
    text = read_text_from_file(INPUT_FILE, CHARS_TO_READ, ENCODING)
    tokens = text_to_tokens(text)
    
    print(f"Loaded {len(text)} characters ({len(tokens)} tokens)")
    
    # Perform merges
    final_tokens, next_token_idx, merge_rules = perform_merges(
        tokens, NUM_MERGES, START_TOKEN_IDX, SHOW_PROGRESS
    )
    
    # Print summary
    print_summary(tokens, final_tokens, next_token_idx, START_TOKEN_IDX, SHOW_TOP_PAIRS)
    
    # Save rules
    save_merge_rules(merge_rules)
    
    total_time = time.time() - start_time
    print(f"\nTotal processing time: {total_time:.2f} seconds")
    
    return merge_rules

# Run the main function
if __name__ == "__main__":
    merge_rules = main()
    
    # Quick test
    test_text = "hello this is a test"
    encoded = encode_text(test_text, merge_rules, START_TOKEN_IDX)
    decoded = decode_text(encoded, merge_rules, START_TOKEN_IDX)
    
    print(f"\n=== QUICK TEST ===")
    print(f"Text: '{test_text}'")
    print(f"Encoded: {len(encoded)} tokens")
    print(f"Decoded: '{decoded}'")
    print(f"Perfect: {test_text == decoded}")



