"""Normalize bounded Claude/Codex transcript evidence without executing it."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections import deque


SECRET = re.compile(
    r"(?i)(?:\b(?:sk-|gh[pousr]_|github_pat_|xox[baprs]-)[A-Za-z0-9_-]{16,}"
    r"|\bBearer\s+[A-Za-z0-9._~+/-]{16,}"
    r"|(?:api[_-]?key|access[_-]?token|password|secret)\s*[=:]\s*[\"']?[^\s\"',}]{8,})"
)


def redact(text):
    return SECRET.sub("[REDACTED]", text)


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()[:24]


def open_transcript(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValueError("transcript must be a regular file")
    return os.fdopen(fd, encoding="utf-8", errors="replace")


def row_count(path):
    with open_transcript(path) as handle:
        return sum(1 for _ in handle)


def text_content(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(text_content(v) for v in value if isinstance(v, (str, dict)))
    if isinstance(value, dict):
        if value.get("type") in {"thinking", "image", "input_image"}:
            return ""
        return text_content(value.get("text", value.get("content", "")))
    return ""


def normalized(row, host):
    if host == "claude":
        if row.get("isMeta") or row.get("type") not in {"user", "assistant"}:
            return []
        message = row.get("message") or {}
        role = message.get("role", row.get("type"))
        content = message.get("content", "")
        if isinstance(content, str):
            return [(role, content)]
        parts = []
        for block in content if isinstance(content, list) else []:
            kind = block.get("type") if isinstance(block, dict) else None
            if kind == "tool_use":
                parts.append(("tool_call", block.get("name", "") + " " + json.dumps(block.get("input", {}))))
            elif kind == "tool_result":
                parts.append(("tool_result", ("ERROR " if block.get("is_error") else "") + text_content(block.get("content", ""))))
            elif kind == "text":
                parts.append((role, block.get("text", "")))
        return parts
    if row.get("type") != "response_item":
        return []
    item = row.get("payload") or {}
    kind = item.get("type")
    if kind == "message" and item.get("role") in {"user", "assistant"}:
        if item.get("phase") == "analysis":
            return []
        return [(item["role"], text_content(item.get("content", "")))]
    if kind in {"function_call", "custom_tool_call"}:
        return [("tool_call", item.get("name", "") + " " + str(item.get("arguments", item.get("input", ""))))]
    if kind in {"function_call_output", "custom_tool_call_output"}:
        return [("tool_result", text_content(item.get("output", "")))]
    return []


def read_evidence(path, cutoff, host, session, *, max_rows=240):
    tail = deque(maxlen=max_rows-8)
    users = deque(maxlen=8)
    expected = session.split(":", 1)[-1]
    with open_transcript(path) as handle:
        for number, line in enumerate(handle, 1):
            if number > cutoff:
                break
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict):
                continue
            actual = row.get("sessionId") if host == "claude" else None
            if host == "codex" and row.get("type") == "session_meta":
                actual = (row.get("payload") or {}).get("id")
            if actual and actual != expected:
                raise ValueError("transcript session does not match hook")
            for index, (role, text) in enumerate(normalized(row, host)):
                text = redact(text.strip())[:2400]
                if not text or role not in {"user", "assistant", "tool_call", "tool_result"}:
                    continue
                if role == "user" and text.startswith(("# AGENTS.md instructions", "<environment_context>", "<system-reminder>")):
                    continue
                identifier = "ev-" + digest(f"{session}:{number}:{index}:{text}")
                entry = {"id": identifier, "session": session, "row": number, "role": role, "text": text}
                tail.append(entry)
                if role == "user":
                    users.append(entry)
    return sorted({e["id"]: e for e in [*users, *tail]}.values(), key=lambda e: e["row"])
