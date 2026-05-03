#!/usr/bin/env python3
"""
Doxygen FILTER_PATTERNS script for MDR (Model Description Report) generation.

Doxygen invokes this as:
    python3 scripts/mdr_filter.py /abs/path/to/src/models/<name>.cpp

For each model .cpp the script:
  1. Extracts the model_name() return value via regex.
  2. Classifies MessageBus .publish() / .get() call keys into outputs and inputs.
     - Outputs: any key passed to .publish("key", ...)
     - Inputs:  any key passed to .get("key", ...) that is NOT also published
                (loopback signals that a model reads back from itself are not inputs)
  3. Reads mdrs/<model_name>.dox (the hand-authored MDR template).
  4. Replaces the <!-- SIGNALS --> placeholder with a generated Doxygen signal table.
  5. Wraps the merged result in a Doxygen block comment and emits it, then emits
     the original .cpp content unchanged.

Non-model files (e.g. message_bus.cpp) that have no model_name() are passed
through to stdout without modification.
"""

import sys
import re
import os

REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MDRS_DIR    = os.path.join(REPO_ROOT, "mdrs")
PLACEHOLDER = "<!-- SIGNALS -->"


def extract_model_name(content):
    m = re.search(
        r'model_name\s*\(\s*\)\s*\{[^}]*return\s*"([^"]+)"',
        content, re.DOTALL
    )
    return m.group(1) if m else None


def extract_signals(content):
    published = list(dict.fromkeys(re.findall(r'\.publish\s*\(\s*"([^"]+)"', content)))
    gotten    = list(dict.fromkeys(re.findall(r'\.get\s*\(\s*"([^"]+)"',     content)))
    inputs    = [k for k in gotten if k not in published]
    return inputs, published


def build_signal_table(model_name, inputs, outputs):
    slug  = model_name.replace("-", "_")
    lines = []

    lines.append(f"@subsection mdr_{slug}_inputs Inputs")
    lines.append("")
    if inputs:
        lines.append("| Signal Key | Type | Default |")
        lines.append("|---|---|---|")
        for key in inputs:
            lines.append(f"| `{key}` | double | 0.0 |")
    else:
        lines.append("_None — this model does not read external signals from the message bus._")

    lines.append("")
    lines.append(f"@subsection mdr_{slug}_outputs Outputs")
    lines.append("")
    if outputs:
        lines.append("| Signal Key | Type |")
        lines.append("|---|---|")
        for key in outputs:
            lines.append(f"| `{key}` | double |")
    else:
        lines.append("_None — this model does not publish signals to the message bus._")

    return "\n".join(lines)


def wrap_in_doxygen_block(text):
    body = "\n".join(" * " + line if line.strip() else " *" for line in text.splitlines())
    return "/*!\n" + body + "\n */"


def main():
    cpp_path = sys.argv[1]
    content  = open(cpp_path, encoding="utf-8").read()

    model_name = extract_model_name(content)
    if not model_name:
        sys.stdout.write(content)
        return

    inputs, outputs = extract_signals(content)
    signal_table    = build_signal_table(model_name, inputs, outputs)

    dox_path = os.path.join(MDRS_DIR, model_name + ".dox")
    if os.path.isfile(dox_path):
        template = open(dox_path, encoding="utf-8").read()
        merged = template.replace(PLACEHOLDER, signal_table)
    else:
        merged = (
            f"@page mdr_{model_name} MDR: {model_name}\n\n"
            f"@note No mdrs/{model_name}.dox found. "
            f"Create that file to add a narrative MDR for this model.\n\n"
            f"@section mdr_{model_name}_signals Signal Interface\n\n"
            f"{signal_table}"
        )

    mdr_block = wrap_in_doxygen_block(merged)
    sys.stdout.write(mdr_block + "\n\n")
    sys.stdout.write(content)


if __name__ == "__main__":
    main()
