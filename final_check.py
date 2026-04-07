"""Final comprehensive check"""
with open('test_hfss_syntax.py', 'r') as f:
    content = f.read()

# Count in entire file
total_opens = content.count('[')
total_closes = content.count(']')
print(f"Entire file: {total_opens} [ vs {total_closes} ] = net {total_opens - total_closes}")

# Count in StackUp section (from line 177 to end)
lines = content.split('\n')
stackup_text = '\n'.join(lines[176:])
stackup_opens = stackup_text.count('[')
stackup_closes = stackup_text.count(']')
print(f"StackUp section (line 177-end): {stackup_opens} [ vs {stackup_closes} ] = net {stackup_opens - stackup_closes}")

# Now let's trace through character by character to find the exact issue
stack = []
for i, char in enumerate(content):
    if char == '[':
        stack.append(i)
    elif char == ']':
        if stack:
            stack.pop()
        else:
            # Find line number
            line_num = content[:i].count('\n') + 1
            print(f"❌ Extra ] at position {i}, line {line_num}")
            break

if not stack:
    print("✅ All brackets balanced!")
else:
    print(f"❌ {len(stack)} unclosed [ brackets")
