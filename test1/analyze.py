import re
import sys

log_file = sys.argv[1]
average_diffs = {}

bios_pattern = re.compile(r"Average time difference for (bios[0-6\-]+) .*: (\d+)")

with open(log_file, "r") as f:
    for line in f:
        match = bios_pattern.search(line)
        if match:
            bios_name = match.group(1)
            avg_time = int(match.group(2))
            average_diffs[bios_name] = avg_time

baseline = average_diffs.get("bios-1")
if baseline is None:
    print("bios-1 average time not found.")
    exit(1)

print(f"Baseline (bios-1): {baseline}")
print("Growth relative to bios-1:")

for i in range(0, 7):
    bios_key = f"bios{i}"
    if bios_key in average_diffs:
        current = average_diffs[bios_key]
        diff = current - baseline
        percent = (diff / baseline) * 100
        print(f"{bios_key}: +{diff} ({percent:.4f}%)")
    else:
        print(f"{bios_key}: not found")
