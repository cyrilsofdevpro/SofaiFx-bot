#!/usr/bin/env python3
"""
Monitor log file while running test
"""

import subprocess
import time
import os

log_file = "logs/sofai_fx_20260424.log"

print("Starting test in background...")

# Get current file size
initial_size = os.path.getsize(log_file) if os.path.exists(log_file) else 0

# Run test
proc = subprocess.Popen(['python', 'test_known_user.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Wait a bit for test to run
time.sleep(15)

# Read new log content
if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        f.seek(initial_size)
        new_logs = f.read()
        
    if new_logs:
        print("\n📋 NEW LOG ENTRIES DURING TEST:")
        print("="*80)
        print(new_logs[-2000:])  # Last 2000 chars
        print("="*80)
    else:
        print("❌ No new logs found")
else:
    print("❌ Log file not found")

proc.wait()
