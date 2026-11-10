"""ce.py -- talk to the Cheat Engine MCP bridge over its named pipe.

The bridge (ce_mcp_bridge.lua, loaded by CE) listens on \\\\.\\pipe\\CE_MCP_Bridge_v99 and speaks
length-prefixed JSON-RPC frames: a little-endian u32 length, then the JSON object with
{"method": ..., "params": {...}}.

    python ce.py <method> [json-params]

Prints the JSON answer.
"""

import json
import struct
import sys

import win32file

PIPE = r"\\.\pipe\CE_MCP_Bridge_v99"


def call(method, params=None):
    handle = win32file.CreateFile(
        PIPE,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0,
        None,
        win32file.OPEN_EXISTING,
        0,
        None,
    )
    try:
        req = json.dumps({"method": method, "params": params or {}}).encode("utf-8")
        win32file.WriteFile(handle, struct.pack("<I", len(req)) + req)
        hdr = win32file.ReadFile(handle, 4)[1]
        size = struct.unpack("<I", hdr)[0]
        chunks = []
        left = size
        while left > 0:
            part = win32file.ReadFile(handle, left)[1]
            if not part:
                break
            chunks.append(part)
            left -= len(part)
        return b"".join(chunks).decode("utf-8", "replace")
    finally:
        win32file.CloseHandle(handle)


if __name__ == "__main__":
    m = sys.argv[1]
    p = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    print(call(m, p))
