# -*- coding: utf-8 -*-

from typing import Any

# ----------------------------------------------------------------------------

def debug_print_tree(value: Any) -> None:
    """Pretty-print nested dict/list structures for debugging."""
    def walk(node: Any, prefix: str = "", is_last: bool = True, label: str = "root") -> None:
        connector = "└─ " if is_last else "├─ "
        print(prefix + connector + str(label))
        child_prefix = prefix + ("   " if is_last else "│  ")

        if isinstance(node, dict):
            items = list(node.items())
            for idx, (key, val) in enumerate(items):
                last = idx == len(items) - 1
                if isinstance(val, (dict, list)):
                    walk(val, child_prefix, last, key)
                else:
                    leaf_connector = "└─ " if last else "├─ "
                    print(child_prefix + leaf_connector + f"{key}: {val}")
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                last = idx == len(node) - 1
                if isinstance(item, (dict, list)):
                    walk(item, child_prefix, last, f"[{idx}]")
                else:
                    leaf_connector = "└─ " if last else "├─ "
                    print(child_prefix + leaf_connector + f"[{idx}]: {item}")

    walk(value)
