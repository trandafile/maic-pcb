"""Debug: count brackets as they're generated"""

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

# Find the StackUp section
for i, line in enumerate(lines):
    if 'StackUp' in line and 'SeparatorProp' in line:
        print(f"StackUp section starts at line {i+1}")
        # Count brackets from here to end
        section = '\n'.join(lines[i:])
        opens = section.count('[')
        closes = section.count(']')
        print(f"Brackets in StackUp section to end: {opens} open, {closes} close")
        print(f"Net: {opens - closes}")
        break
