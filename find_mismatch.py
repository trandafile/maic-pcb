"""Find exact location of bracket mismatch"""

with open('test_hfss_syntax.py', 'r') as f:
    lines = f.readlines()

stack = []
for line_num, line in enumerate(lines, 1):
    for col, char in enumerate(line, 1):
        if char == '[':
            stack.append((line_num, col))
        elif char == ']':
            if stack:
                stack.pop()
            else:
                print(f'❌ Extra ] at line {line_num}, col {col}')
                print(f'   Content: {line.rstrip()}')
                print(f'   Stack depth was 0')
                break
    else:
        continue
    break

if not stack:
    print('✅ All brackets balanced in section analyzed')
else:
    print(f'❌ {len(stack)} unclosed [')
    for ln, col in stack[-3:]:
        print(f'   Line {ln}, col {col}: {lines[ln-1].rstrip()}')
