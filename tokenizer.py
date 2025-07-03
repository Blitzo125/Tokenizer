# ============================================================================
# HIGHLY OPTIMIZED TOKENIZER - CONFIGURATION SECTION
# ============================================================================
INPUT_FILE = 'input.txt'
CHARS_TO_READ = 50000
ENCODING = 'utf-8'
NUM_MERGES = 500
START_TOKEN_IDX = 256
SHOW_TOP_PAIRS = 10
SHOW_PROGRESS = False
SAVE_RULES = True
OVERWRITE_RULES = True
RULES_FILENAME = 'merge_rules.json'
PAIRS_PER_ITERATION = 10
# ============================================================================

from collections import Counter
import json
import time
import os

def read_text_from_file(filename, num_chars=None, encoding='utf-8'):
    with open(filename, 'r', encoding=encoding) as file:
        return file.read() if num_chars is None else file.read(num_chars)

def text_to_tokens(text):
    return list(text.encode('utf-8'))

def find_token_pairs(tokens):
    return [tuple(tokens[i:i+2]) for i in range(len(tokens) - 1)]

def count_pair_frequencies(token_pairs):
    return Counter(token_pairs)

def get_most_frequent_pairs(pair_counts, num_pairs):
    return pair_counts.most_common(num_pairs)

def merge(ids, pair, idx):
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

def perform_merges(tokens, num_merges, start_token_idx, show_progress=True, pairs_per_iteration=10):
    current_tokens = tokens.copy()
    next_token_idx = start_token_idx
    merge_rules = []
    start_time = time.time()
    total_merges = 0
    
    for merge_iteration in range(num_merges):
        token_pairs = find_token_pairs(current_tokens)
        if not token_pairs:
            break
        
        pair_counts = count_pair_frequencies(token_pairs)
        top_pairs = pair_counts.most_common(pairs_per_iteration)
        valid_pairs = [(pair, count) for pair, count in top_pairs if count >= 2]
        
        if not valid_pairs:
            break
        
        if show_progress and merge_iteration % 10 == 0:
            elapsed = time.time() - start_time
            print(f"Iteration {merge_iteration + 1}/{num_merges} - {len(valid_pairs)} pairs - {elapsed:.2f}s")
        
        initial_count = len(current_tokens)
        merged_count = 0
        
        for pair, count in valid_pairs:
            merge_rules.append({
                'pair': pair,
                'new_token': next_token_idx,
                'count': count
            })
            
            current_tokens = merge(current_tokens, pair, next_token_idx)
            next_token_idx += 1
            merged_count += 1
            total_merges += 1
            
            if len(current_tokens) <= 1:
                break
        
        if show_progress and merge_iteration % 10 == 0:
            final_count = len(current_tokens)
            reduction = initial_count - final_count
            print(f"  Merged {merged_count} pairs: {initial_count} → {final_count} (-{reduction})")
        
        if len(current_tokens) <= 1:
            break
    
    total_time = time.time() - start_time
    if show_progress:
        print(f"Completed {total_merges} merges in {total_time:.2f}s")
    
    return current_tokens, next_token_idx, merge_rules

def encode_text(text, merge_rules, start_token_idx=256):
    tokens = text_to_tokens(text)
    for rule in merge_rules:
        tokens = merge(tokens, rule['pair'], rule['new_token'])
    return tokens

def decode_text(tokens, merge_rules, start_token_idx=256):
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
        return f"[Decoding failed: {current_tokens}]"

def save_merge_rules(merge_rules, filename='merge_rules.json', overwrite=True):
    if not overwrite and os.path.exists(filename):
        print(f"File {filename} exists. Set OVERWRITE_RULES=True to overwrite.")
        return
    
    with open(filename, 'w') as f:
        json.dump(merge_rules, f, indent=2)
    print(f"Saved {len(merge_rules)} rules to {filename}")

def load_merge_rules(filename='merge_rules.json'):
    with open(filename, 'r') as f:
        return json.load(f)

def print_summary(original_tokens, final_tokens, next_token_idx, start_token_idx, show_top_pairs):
    print(f"\n=== SUMMARY ===")
    print(f"Original: {len(original_tokens)} tokens")
    print(f"Final: {len(final_tokens)} tokens")
    
    compression = ((len(original_tokens) - len(final_tokens)) / len(original_tokens) * 100)
    print(f"Compression: {compression:.1f}%")
    print(f"Vocabulary: {next_token_idx - start_token_idx} new tokens")
    


def main():
    print("=== TOKENIZER ===")
    start_time = time.time()
    
    print(f"Reading {INPUT_FILE}...")
    text = read_text_from_file(INPUT_FILE, CHARS_TO_READ, ENCODING)
    tokens = text_to_tokens(text)
    
    print(f"Loaded {len(text)} chars ({len(tokens)} tokens)")
    print(f"Merging {PAIRS_PER_ITERATION} pairs per iteration")
    
    print(f"Starting {NUM_MERGES} iterations...")
    final_tokens, next_token_idx, merge_rules = perform_merges(
        tokens, NUM_MERGES, START_TOKEN_IDX, SHOW_PROGRESS, PAIRS_PER_ITERATION
    )
    
    print_summary(tokens, final_tokens, next_token_idx, START_TOKEN_IDX, SHOW_TOP_PAIRS)
    
    if SAVE_RULES:
        save_merge_rules(merge_rules, RULES_FILENAME, OVERWRITE_RULES)
    else:
        print("Skipping save")
    
    total_time = time.time() - start_time
    print(f"Total time: {total_time:.2f}s")
    
    return merge_rules

if __name__ == "__main__":
    merge_rules = main()
    
    print(f"\n=== TEST ===")
    test_text = "hello this is a test"
    encoded = encode_text(test_text, merge_rules, START_TOKEN_IDX)
    decoded = decode_text(encoded, merge_rules, START_TOKEN_IDX)
    
    print(f"Text: '{test_text}'")
    print(f"Encoded: {len(encoded)} tokens")
    print(f"Decoded: '{decoded}'")
    print(f"Perfect: {test_text == decoded}")
    
    if test_text == decoded:
        print("✓ Working!")
    else:
        print("✗ Issues!")



