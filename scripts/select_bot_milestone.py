#!/usr/bin/env python3
"""Select a trusted, bounded GitHub coding-agent milestone from issue metadata.

Only exact Bot milestone [focus] issue titles are accepted. Issue text is
untrusted task metadata; it is never executed or passed to a shell/model.
"""
import argparse
import json
import re
import sys

FOCI = ("tween", "face")
TITLE = re.compile(r"^Bot milestone \[(tween|face)\]: [A-Za-z0-9][A-Za-z0-9 .,()'/-]{7,110}$")


def select(issues, slot):
    if not isinstance(issues, list) or type(slot) is not int or slot < 0:
        raise ValueError("Invalid issue list or runner slot")
    eligible = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        number, title = issue.get("number"), issue.get("title")
        if type(number) is not int or number < 1 or type(title) is not str:
            continue
        match = TITLE.fullmatch(title)
        if match is not None and match.group(1) in FOCI:
            eligible.append((number, match.group(1)))
    if eligible:
        issue, focus = min(eligible)
        return {"focus": focus, "issue": issue, "source": "issue"}
    return {"focus": FOCI[slot % len(FOCI)], "issue": 0, "source": "rotation"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot", type=int, required=True)
    args = parser.parse_args()
    try:
        result = select(json.load(sys.stdin), args.slot)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(1, "Bot milestone queue invalid: " + str(exc) + "\n")
    # shell parses JSON as data, never evaluates untrusted issue titles
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
