#!/usr/bin/env python3
"""ADLC helper. Standard library only, so it runs in any repo and any CI.

  adlc.py tier [--map FILE] [PATH ...]    print T1, T2 or T3 for the paths (stdin if none)
  adlc.py check-protected [--list FILE]   Claude Code PreToolUse hook: block edits to protected paths
  adlc.py review-rounds --reviewers A,B   count review rounds in `gh api .../reviews` JSON on stdin
"""
import argparse
import json
import os
import re
import sys

TIERS = ("T1", "T2", "T3")
DEFAULT_TIER = "T2"


def glob_to_regex(pattern):
    """Translate a path glob to a regex. `**` crosses directories, `*` and `?` do not."""
    i, out = 0, []
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def read_rules(path):
    """Return [(tier_or_None, regex)] from a rules file; a missing file means no rules."""
    rules = []
    if not os.path.exists(path):
        return rules
    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            if parts[0] in TIERS:
                if len(parts) != 2:
                    sys.exit(f"{path}:{n}: expected '<tier> <glob>', got: {raw.strip()}")
                rules.append((parts[0], glob_to_regex(parts[1])))
            elif len(parts) == 1:
                rules.append((None, glob_to_regex(parts[0])))
            else:
                sys.exit(f"{path}:{n}: unknown tier {parts[0]!r}")
    return rules


def normalize(path):
    path = path.strip()
    while path.startswith("./"):
        path = path[2:]
    return path


def tier_of(path, rules):
    hits = [t for t, rx in rules if rx.match(path)]
    return max(hits) if hits else DEFAULT_TIER


def cmd_tier(args):
    rules = read_rules(args.map)
    paths = args.paths or [line for line in sys.stdin.read().splitlines()]
    paths = [normalize(p) for p in paths if p.strip()]
    if not paths:
        print("T1")
        return 0
    result = "T1"
    for p in paths:
        t = tier_of(p, rules)
        if args.explain:
            print(f"{t} {p}", file=sys.stderr)
        result = max(result, t)
    print(result)
    return 0


def cmd_check_protected(args):
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    rules = read_rules(os.path.join(project, args.list) if project and not os.path.isabs(args.list) else args.list)
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    tool_input = event.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not target:
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    cwd = event.get("cwd") or root
    rel = os.path.relpath(os.path.abspath(os.path.join(cwd, target)), root)
    for _, rx in rules:
        if rx.match(rel):
            print(
                f"ADLC: {rel} is protected (listed in {args.list}). "
                "Ask the owner, or change the list in a separate PR.",
                file=sys.stderr,
            )
            return 2
    return 0


def cmd_review_rounds(args):
    """A round is one submitted review by a listed reviewer. COMMENTED, CHANGES_REQUESTED
    and APPROVED all count; PENDING and DISMISSED do not."""
    reviewers = {r.strip().lower() for r in args.reviewers.split(",") if r.strip()}
    reviews = json.load(sys.stdin)
    rounds = sum(
        1
        for r in reviews
        if (r.get("user") or {}).get("login", "").lower() in reviewers
        and r.get("state") in ("COMMENTED", "CHANGES_REQUESTED", "APPROVED")
    )
    print(rounds)
    return 0


def main():
    p = argparse.ArgumentParser(prog="adlc.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tier")
    t.add_argument("--map", default=".adlc/tiers")
    t.add_argument("--explain", action="store_true")
    t.add_argument("paths", nargs="*")
    c = sub.add_parser("check-protected")
    c.add_argument("--list", default=".adlc/protected")
    r = sub.add_parser("review-rounds")
    r.add_argument("--reviewers", required=True)
    args = p.parse_args()
    return {"tier": cmd_tier, "check-protected": cmd_check_protected, "review-rounds": cmd_review_rounds}[
        args.cmd
    ](args)


if __name__ == "__main__":
    sys.exit(main())
