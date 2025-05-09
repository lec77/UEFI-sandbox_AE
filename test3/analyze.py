import sys
from collections import defaultdict

filepath = sys.argv[1]

# Read all lines from the specified file
with open(filepath, 'r') as f:
    lines = f.readlines()

# Extract lines between "Start of SandboxTestClient" and "ASSERT"
capture = False
relevant_lines = []
for line in lines:
    line = line.strip()
    if 'Start of SandboxTestClient' in line:
        capture = True
        continue
    if 'End of SandboxTestClient' in line:
        break
    if capture:
        relevant_lines.append(line)

# Group lines into blocks starting with "Parts, TSC"
blocks = []
current_block = []
for line in relevant_lines:
    if line == 'Parts,TSC':
        if current_block:
            blocks.append(current_block)
        current_block = []
    else:
        current_block.append(line)
if current_block:
    blocks.append(current_block)

TestNames = ['Simple Call', 'Input Object', 'Input Buffer', 'Output Buffer']

print("Results of micro tests.")

# For each block, compute average per part after excluding min and max
for block_index, block in enumerate(blocks):
    part_values = defaultdict(list)
    for entry in block:
        if ',' not in entry:
            continue
        part, value = entry.split(',')
        part = part.strip()
        value = int(value.strip())
        part_values[part].append(value)

    print(f"\n{TestNames[block_index]} Test")
    for part, values in part_values.items():
        if len(values) < 3:
            print(f"{part}: Not enough data to exclude min/max")
            continue
        trimmed = sorted(values)[1:-1]  # Remove min and max
        avg = sum(trimmed) / len(trimmed)
        print(f"{part}: {avg:.2f}")
