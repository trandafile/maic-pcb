"""Check each ChangeProperty call"""
with open('test_hfss_syntax.py', 'r') as f:
    lines = f.readlines()

# Find all ChangeProperty calls
cp_starts = []
for i, line in enumerate(lines):
    if 'ChangeProperty(' in line:
        cp_starts.append(i)

print(f"Found {len(cp_starts)} ChangeProperty calls at lines: {[i+1 for i in cp_starts]}")

# Check each section
for idx, start in enumerate(cp_starts):
    end = cp_starts[idx+1] if idx+1 < len(cp_starts) else len(lines)
    section = ''.join(lines[start:end])
    opens = section.count('[')
    closes = section.count(']')
    net = opens - closes
    status = "✅" if net == 0 else "❌"
    print(f"{status} Lines {start+1}-{end}: {opens} [ vs {closes} ] = net {net}")
