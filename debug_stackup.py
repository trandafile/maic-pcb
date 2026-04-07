"""Debug: Generate and count brackets in StackUp section only"""

from core import hfss_exporter

data = {
    "layers": [
        {"id": "L2", "name": "L2 - Top Copper", "type": "metal", "thickness": 0.035, "color_hex": "#CC5500"},
        {"id": "D1", "name": "D1 - FR4 Core", "type": "dielectric", "thickness": 1.5, "color_hex": "#708090"},
        {"id": "L1", "name": "L1 - Bottom Copper", "type": "metal", "thickness": 0.035, "color_hex": "#CC5500"}
    ]
}

script = hfss_exporter.generate_hfss_script(data)
lines = script.split('\n')

# Find StackUp section
for i, line in enumerate(lines):
    if 'NAME:StackUp' in line and 'SeparatorProp' in line:
        # Extract from this line to end
        stackup_section = '\n'.join(lines[i:])
        opens = stackup_section.count('[')
        closes = stackup_section.count(']')
        
        print(f"StackUp section (from line {i+1} to end):")
        print(f"  Opening brackets: {opens}")
        print(f"  Closing brackets: {closes}")
        print(f"  Net: {opens - closes}")
        
        # Now count line by line
        print("\nDetailed bracket count per line:")
        balance = 0
        for j, l in enumerate(lines[i:], i+1):
            o = l.count('[')
            c = l.count(']')
            balance += o - c
            if o > 0 or c > 0:
                print(f"  Line {j}: +{o} -{c} = balance {balance}")
        
        break
