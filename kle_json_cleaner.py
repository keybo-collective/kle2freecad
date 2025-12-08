# -*- coding: utf-8 -*-

import json
from copy import deepcopy

_IDENTIFIER_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")

# ............................................................................

def _ensure_bounding_array(raw: str) -> str:
    """Add a top-level [] wrapper when missing."""
    start = 0
    end = len(raw) - 1

    while start <= end and raw[start].isspace():
        start += 1
    while end >= start and raw[end].isspace():
        end -= 1

    if start > end or raw[start] != "[":
        return f"[{raw}]"

    depth = 0
    in_string = False
    escape = False
    i = start
    while i <= end:
        ch = raw[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    j = i + 1
                    while j <= end and raw[j].isspace():
                        j += 1
                    if j > end:
                        return raw
                    return f"[{raw}]"
            if depth < 0:
                return f"[{raw}]"
        i += 1

    return f"[{raw}]"

# ----------------------------------------------------------------------------

def sanitizeAsJson(raw: str) -> str:
    """
    Convert JSON-like strings with unquoted object keys into valid JSON.
    """

    try:
        # Fast path: already valid JSON? return as-is.
        json.loads(raw)
        return raw
    except Exception:
        pass

    wrapped = _ensure_bounding_array(raw)
    rescape_strings = "\\n" not in raw
    out = []
    stack = []
    expecting_key = False

    i = 0
    length = len(wrapped)
    while i < length:
        ch = wrapped[i]

        if ch == '"':
            if rescape_strings:
                i += 1
                buf = []
                length_minus_one = length - 1
                while i < length:
                    ch2 = wrapped[i]
                    if ch2 == '"':
                        k = i + 1
                        while k < length and wrapped[k].isspace():
                            k += 1
                        if k > length_minus_one or wrapped[k] in ",]}":
                            i += 1
                            break
                        buf.append(ch2)
                        i += 1
                        continue
                    if ch2 == "\n":
                        buf.append("\\n")
                        i += 1
                        continue
                    if ch2 == "\r":
                        buf.append("\\r")
                        i += 1
                        continue
                    if ch2 == "\t":
                        buf.append("\\t")
                        i += 1
                        continue
                    buf.append(ch2)
                    i += 1
                out.append('"')
                out.append(json.dumps("".join(buf))[1:-1])
                out.append('"')
                continue

            i += 1
            out.append('"')
            escape = False
            while i < length:
                ch2 = wrapped[i]
                if ch2 == "\n":
                    out.append("\\n")
                    escape = False
                    i += 1
                    continue
                if ch2 == "\r":
                    out.append("\\r")
                    escape = False
                    i += 1
                    continue
                if ch2 == "\t":
                    out.append("\\t")
                    escape = False
                    i += 1
                    continue
                out.append(ch2)
                if escape:
                    escape = False
                elif ch2 == "\\":
                    escape = True
                elif ch2 == '"':
                    i += 1
                    break
                i += 1
            continue

        if ch == "{":
            stack.append("{")
            expecting_key = True
            out.append(ch)
            i += 1
            continue

        if ch == "[":
            stack.append("[")
            expecting_key = False
            out.append(ch)
            i += 1
            continue

        if ch == "}":
            if stack and stack[-1] == "{":
                stack.pop()
            expecting_key = bool(stack and stack[-1] == "{")
            out.append(ch)
            i += 1
            continue

        if ch == "]":
            if stack and stack[-1] == "[":
                stack.pop()
            expecting_key = bool(stack and stack[-1] == "{")
            out.append(ch)
            i += 1
            continue

        if ch == ",":
            out.append(ch)
            expecting_key = bool(stack and stack[-1] == "{")
            i += 1
            continue

        if ch == ":":
            expecting_key = False
            out.append(ch)
            i += 1
            continue

        if expecting_key:
            if ch.isspace():
                out.append(ch)
                i += 1
                continue

            if ch == "'":
                key_start = i + 1
                key_end = key_start
                while key_end < length and wrapped[key_end] != "'":
                    key_end += 1
                out.append(f'"{wrapped[key_start:key_end]}"')
                i = key_end + 1
                expecting_key = False
                continue

            key_start = i
            while i < length and wrapped[i] in _IDENTIFIER_CHARS:
                i += 1

            if i > key_start:
                out.append(f'"{wrapped[key_start:i]}"')
                expecting_key = False
                continue

            expecting_key = False

        out.append(ch)
        i += 1

    return "".join(out)

# ----------------------------------------------------------------------------

def normalizeKLEData(data):
    """
    Normalize a 2D array-like structure so second-level string entries become dicts with key `_v`.
    Assumes `data` is a list of lists; mutates in place for speed and returns the same reference.
    """

    # This loop (1) checks for single row layouts
    oneDim = False
    for row in data:
        if not isinstance(row, list):
            oneDim = True
            break
    if oneDim:
        flat = deepcopy(list(data))
        data[:] = [flat]

    # This loop (2) compounds param pre-values with key values
    for row in data:
        if not isinstance(row, list):
            continue
        idx = 0
        normalized = []
        length = len(row)
        while idx < length:
            item = row[idx]
            if isinstance(item, dict):
                if idx + 1 < length and isinstance(row[idx + 1], str):
                    item["v"] = row[idx + 1]
                    idx += 1
                normalized.append(item)
            elif isinstance(item, str):
                normalized.append({"v": item})
            else:
                normalized.append(item)
            idx += 1
        row[:] = normalized

    # This loop (3) adjusts all the keys' dimensions
    oy = -1 # origin Y
    g_state = False # Ghost state
    d_state = False # Decal state
    for row in data:
        oy += 1
        ox = 0 # reset origin X
        if not isinstance(row, list):
            continue
        for idx, item in enumerate(row):
            if not isinstance(item, dict):
                continue # already cleaned out in loop 1, but just in case
            normalized_item = {
                "v": item.get("v", ""), # don't need this, but helpful in debug
                "w": item.get("w", 1),
                "h": item.get("h", 1),
                "x": item.get("x", 0),
                "y": item.get("y", 0),
            }
            if "w2" in item:
                normalized_item["w2"] = item["w2"]
            if "h2" in item:
                normalized_item["h2"] = item["h2"]
            if "l" in item:
                normalized_item["l"] = item["l"]

            if "g" in item:
                g_state = bool(item["g"])
            if "d" in item:
                d_state = bool(item["d"])

            if g_state:
                normalized_item["g"] = True
            if d_state:
                normalized_item["d"] = True

            w_val = normalized_item["w"]
            h_val = normalized_item["h"]
            if (w_val >= 2) or (h_val >= 2):
                a_val = 0
                if h_val > w_val: a_val = 90
                normalized_item["s"] = True
                if "_rs" in item:
                    a_val += item.get("_rs")
                normalized_item["r"] = a_val

            # x is origin-x + given x
            normalized_item["x"] += ox
            # new origin-x is x + width (width already set to 1)
            ox = normalized_item["x"] + normalized_item["w"]

            # y is origin-y + given y
            normalized_item["y"] += oy
            # new origin-y is y
            oy = normalized_item["y"]

            row[idx] = normalized_item

    return data

# ----------------------------------------------------------------------------

def countRows(obj):
    """Return the max y-coordinate plus height across all keys in the layout."""
    if not isinstance(obj, list):
        return 0
    max_y = 0
    for row in obj:
        if not isinstance(row, list):
            continue
        for item in row:
            if isinstance(item, dict):
                e = item.get("y", 0) + item.get("h", 1)
                if e > max_y:
                    max_y = e
    return max_y

# ----------------------------------------------------------------------------

def countCols(obj):
    """Return the max x-coordinate plus width across all keys in the layout."""
    if not isinstance(obj, list):
        return 0
    max_x = 0
    for row in obj:
        if not isinstance(row, list):
            continue
        for item in row:
            if isinstance(item, dict):
                e = item.get("x", 0) + item.get("w", 1)
                if e > max_x:
                    max_x = e
    return max_x

# ----------------------------------------------------------------------------

def countKeys(obj):
    """Return the count of all keys in the structure."""
    if not isinstance(obj, list):
        return 0
    count = 0
    for row in obj:
        if not isinstance(row, list):
            continue
        for item in row:
            if isinstance(item, dict):
                count += 1
    return count
