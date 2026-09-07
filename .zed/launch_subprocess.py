#!/usr/bin/env python3
"""
Generic subprocess launcher for Zed debugger configs.

Debugpy cannot launch compiled binaries directly (it reads the file as Python
source). This script acts as a thin Python shim: Debugpy runs this file, and
it forwards all arguments to subprocess.run().

Usage in debug.json:
    "program": "$ZED_WORKTREE_ROOT/.zed/launch_subprocess.py",
    "args": ["/path/to/binary", "arg1", "arg2", ...]

Environment variables set via the "env" field in debug.json are inherited
automatically by the subprocess.
"""
import subprocess
import sys

if len(sys.argv) < 2:
    print("Error: no command specified.", file=sys.stderr)
    print("Pass the executable and its arguments via 'args' in debug.json.", file=sys.stderr)
    sys.exit(1)

result = subprocess.run(sys.argv[1:])
sys.exit(result.returncode)
