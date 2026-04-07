"""Validate bracket matching in HFSS script"""

def validate_brackets(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    stack = []
    line_num = 0
    for i, char in enumerate(content):
        if char == '\n':
            line_num += 1
        if char in '([{':
            stack.append((char, line_num))
        elif char in ')]}':
            if not stack:
                print(f"Error at line {line_num}: unexpected closing '{char}'")
                return False
            opening, open_line = stack.pop()
            pairs = {'(': ')', '[': ']', '{': '}'}
            if pairs[opening] != char:
                print(f"Error at line {line_num}: '{char}' does not match '{opening}' from line {open_line}")
                print(f"Stack has {len(stack)} items")
                return False
    
    if stack:
        print(f"Error: {len(stack)} unclosed brackets:")
        for opening, line in stack[-5:]:  # Show last 5
            print(f"  '{opening}' opened at line {line}")
        return False
    
    print("✅ All brackets matched correctly!")
    return True

if __name__ == '__main__':
    validate_brackets('test_hfss_syntax.py')
