_IDENTIFIER_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")


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


def preParse(raw: str) -> str:
    """
    Convert JSON-like strings with unquoted object keys into valid JSON.
    """
    wrapped = _ensure_bounding_array(raw)
    out = []
    stack = []
    in_string = False
    escape = False
    expecting_key = False

    i = 0
    length = len(wrapped)
    while i < length:
        ch = wrapped[i]

        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            out.append(ch)
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

def postParse(data):
    """
    Normalize a 2D array-like structure so second-level string entries become dicts with key `_v`.
    Assumes `data` is a list of lists; mutates in place for speed and returns the same reference.
    """

    # This loop (1) compounds param pre-values with key values
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

    # This loop (2) adjusts all the keys' dimensions
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
                # "v": item.get("v", ""), # don't need this, but helpful in debug
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


def count_rows(obj):
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


def count_cols(obj):
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
