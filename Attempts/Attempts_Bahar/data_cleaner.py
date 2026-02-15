import json

def load_and_examine_data(json_file):
    # Load your JSON file with proper encoding
    with open(json_file, 'r', encoding='utf-8') as f:  # ← Added encoding='utf-8'
        data = json.load(f)
    
    # Let's see what we have
    print(f"Total lines: {len(data['lines'])}")
    print(f"Page size: {data['metadata']['page_dimensions']}")
    
    # Look at first 5 lines
    print("\nFirst 5 lines:")
    for i in range(5):
        line = data['lines'][i]
        print(f"Line {i}: from ({line['start_x']}, {line['start_y']}) to ({line['end_x']}, {line['end_y']}) - length: {line['length']}")
    
    return data

def clean_lines(lines):
    print("Cleaning lines...")
    
    # Keep lines that are longer than 0.01 (very small threshold)
    good_lines = []
    zero_length_count = 0
    
    for line in lines:
        if line['length'] > 0.01:  # Much smaller threshold
            good_lines.append(line)
        else:
            zero_length_count += 1
    
    print(f"Removed {zero_length_count} zero-length lines")
    print(f"Kept {len(good_lines)} out of {len(lines)} lines")
    
    return good_lines

def analyze_line_lengths(lines):
    """Let's see what lengths we actually have"""
    lengths = [line['length'] for line in lines if line['length'] > 0]
    
    print(f"Shortest line: {min(lengths)}")
    print(f"Longest line: {max(lengths)}")
    print(f"Average line length: {sum(lengths)/len(lengths):.2f}")
    
    # Count by length ranges
    very_short = len([l for l in lengths if l < 1])
    short = len([l for l in lengths if 1 <= l < 10])
    medium = len([l for l in lengths if 10 <= l < 50])
    long = len([l for l in lengths if l >= 50])
    
    print(f"Very short lines (< 1): {very_short}")
    print(f"Short lines (1-10): {short}")
    print(f"Medium lines (10-50): {medium}")
    print(f"Long lines (50+): {long}")

# Test it
# Test it
if __name__ == "__main__":
    data = load_and_examine_data('floorplan_data.json')  # ← Changed filename
    
    # Analyze what we have
    analyze_line_lengths(data['lines'])
    
    # Clean the data
    clean_lines_data = clean_lines(data['lines'])