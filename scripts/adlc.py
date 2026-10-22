#!/usr/bin/env python3
"""ADLC helper. Standard library only, so it runs in any repo and any CI.
Repos get a copy at .adlc/scripts/adlc.py from `sync`. Edit it only in the ADLC repo.

  adlc.py tier [--map FILE] [PATH ...]    print T1, T2 or T3 for the paths (stdin if none)
  adlc.py check-protected [--list FILE]   Claude Code PreToolUse hook: block edits to protected paths
  adlc.py protected-changes --base SHA --head SHA [--list FILE]
                                          CI: fail if a PR commit edits a path its parent commit protects
  adlc.py review-rounds --reviewers A,B   count review rounds in `gh api .../reviews` JSON on stdin
  adlc.py pr-title TITLE                  check a PR title against Conventional Commits 1.0.0
  adlc.py changelog-draft --current X.Y.Z --repo OWNER/NAME
                                          next SemVer version and a Common Changelog draft from
                                          `git log --format='%h%x1f%s%x1f%b%x1e' vX.Y.Z..HEAD` on stdin
  adlc.py changelog-entry VERSION [--file CHANGELOG.md]
                                          print one release's entry (for release notes); fail if missing
  adlc.py sync TARGET [--releases] [--check]
                                          from an ADLC checkout at a release tag: write the ADLC's files
                                          into the repo at TARGET (see docs/sync.md)
  adlc.py manifest [--write | --check]    in the ADLC repo: the hashes the drift job in adlc.yml compares
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
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


def parse_rules(lines, source):
    """Return [(tier_or_None, regex)] from the lines of a rules file."""
    rules = []
    for n, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if parts[0] in TIERS:
            if len(parts) != 2:
                sys.exit(f"{source}:{n}: expected '<tier> <glob>', got: {raw.strip()}")
            rules.append((parts[0], glob_to_regex(parts[1])))
        elif len(parts) == 1:
            rules.append((None, glob_to_regex(parts[0])))
        else:
            sys.exit(f"{source}:{n}: unknown tier {parts[0]!r}")
    return rules


def read_rules(path):
    """Return [(tier_or_None, regex)] from a rules file; a missing file means no rules."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return parse_rules(f, path)


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
                "Ask the owner if the list is wrong.",
                file=sys.stderr,
            )
            return 2
    return 0


def git(*args):
    p = subprocess.run(["git", *args], capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"adlc.py: git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout


def protected_at(commit, path):
    """The protected list as it was at a commit: (set of its lines, rules). Empty if the file was absent."""
    p = subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True, text=True)
    lines = p.stdout.splitlines() if p.returncode == 0 else []
    entries = {line.split("#", 1)[0].strip() for line in lines} - {""}
    return entries, parse_rules(lines, f"{commit}:{path}")


EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def is_ancestor(a, b):
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b], capture_output=True).returncode == 0


def cmd_protected_changes(args):
    """Check each PR commit against the list in its first parent, so a failing test protected by an
    earlier commit of the same PR is covered. Once a commit removes a line, it and every later commit
    may change only the list, so a PR cannot unprotect a test and then edit it.
    A merge counts as one commit. A merge of the base branch counts only its hand edits, and lines
    the base removed, because the base was checked on its own.
    Limit: a branch squashed or force-pushed before CI hides the commit order."""
    commits = git("rev-list", "--reverse", "--first-parent", f"{args.base}..{args.head}").split()
    problems, removed_in = [], None
    for c in commits:
        first, *others = git("rev-list", "--parents", "-n", "1", c).split()[1:] or [EMPTY_TREE]
        before, rules = protected_at(first, args.list)
        after, _ = protected_at(c, args.list)
        if others and all(is_ancestor(p, args.base) for p in others):
            diff = git("diff-tree", "-c", "-r", "--no-commit-id", "--name-only", "-z", c)
            for p in others:
                mb = git("merge-base", first, p).strip()
                before -= protected_at(mb, args.list)[0] - protected_at(p, args.list)[0]
        else:
            diff = git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", first, c)
        files = [f for f in diff.split("\0") if f]
        for f in files:
            if any(rx.match(f) for _, rx in rules):
                problems.append(f"{c[:7]} edits {f}, which {args.list} lists.")
        if before - after and not removed_in:
            removed_in = c[:7]
        others = [f for f in files if f != args.list]
        if removed_in and others:
            problems.append(
                f"{c[:7]} changes {', '.join(others)} after {removed_in} removed lines from {args.list}. "
                "Remove lines only at the end of a PR, in commits that change nothing else."
            )
    for problem in problems:
        print(f"ADLC: {problem}", file=sys.stderr)
    if problems:
        print("ADLC: a fix must not change its failing test. Ask the owner if the list is wrong.", file=sys.stderr)
        return 1
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


# Conventional Commits 1.0.0 header: type, optional (scope), optional !, colon, space, description.
TITLE_RE = re.compile(r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^()]+)\))?(?P<bang>!)?: (?P<desc>\S.*)$")
# feat and fix come from the spec; the rest are the commitlint config-conventional types it cites.
TYPES = ("feat", "fix", "build", "chore", "ci", "docs", "perf", "refactor", "revert", "style", "test")
BREAKING_FOOTER = re.compile(r"^BREAKING[ -]CHANGE: ", re.M)
SEMVER_RE = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
PR_REF = re.compile(r" \(#(\d+)\)$")
# Common Changelog categories, in its order. Types not listed here are maintenance noise.
GROUP_OF = {"feat": "Added", "fix": "Fixed", "perf": "Changed", "refactor": "Changed", "revert": "Changed"}
GROUPS = ("Changed", "Added", "Removed", "Fixed")


def parse_title(title):
    """Return (type, breaking, description) or None if not a Conventional Commits header."""
    m = TITLE_RE.match(title.strip())
    if not m or m.group("type").lower() not in TYPES:
        return None
    return m.group("type").lower(), bool(m.group("bang")), m.group("desc")


def cmd_pr_title(args):
    if parse_title(args.title):
        return 0
    print(
        f"ADLC: PR title {args.title!r} is not a Conventional Commit. Use '<type>[(scope)][!]: <description>' "
        f"with type one of {', '.join(TYPES)}. Example: 'fix(api): reject empty names'.",
        file=sys.stderr,
    )
    return 1


def cmd_changelog_draft(args):
    m = SEMVER_RE.match(args.current)
    if not m:
        sys.exit(f"adlc.py: --current {args.current!r} is not MAJOR.MINOR.PATCH")
    major, minor, patch = (int(x) for x in m.groups())
    url = f"https://github.com/{args.repo}"
    groups = {g: [] for g in GROUPS}
    left_out, bump = [], None
    for record in sys.stdin.read().split("\x1e"):
        fields = record.strip("\n").split("\x1f")
        if len(fields) < 2 or not fields[0].strip():
            continue
        sha, subject, body = fields[0].strip(), fields[1].strip(), (fields[2] if len(fields) > 2 else "")
        pr = PR_REF.search(subject)
        if pr:
            subject = subject[: pr.start()]
        parsed = parse_title(subject)
        if not parsed:
            left_out.append(f"{sha} {subject} (not a Conventional Commit)")
            continue
        type_, breaking, desc = parsed
        breaking = breaking or bool(BREAKING_FOOTER.search(body))
        group = "Changed" if breaking else GROUP_OF.get(type_)
        if not group:
            left_out.append(f"{sha} {subject}")
            continue
        refs = f"([`{sha}`]({url}/commit/{sha}))"
        if pr:
            refs += f" ([#{pr.group(1)}]({url}/pull/{pr.group(1)}))"
        text = desc[0].upper() + desc[1:]
        line = f"- **Breaking:** {desc[0].lower() + desc[1:]} {refs}" if breaking else f"- {text} {refs}"
        groups[group].append((not breaking, line))
        level = 3 if breaking else 2 if type_ == "feat" else 1
        bump = max(bump or 0, level)
    if not bump:
        print("No user-facing changes since the last release; no new version.", file=sys.stderr)
        return 3
    if major == 0 and bump == 3:
        bump = 2  # SemVer item 4: in 0.y.z anything may change, so breaking bumps MINOR.
    version = {3: f"{major + 1}.0.0", 2: f"{major}.{minor + 1}.0", 1: f"{major}.{minor}.{patch + 1}"}[bump]
    date = args.date or datetime.date.today().isoformat()
    out = [f"## [{version}] - {date}", ""]
    for g in GROUPS:
        if groups[g]:
            # Breaking changes first; otherwise keep git log order, which is latest-first.
            out += [f"### {g}", "", *(line for _, line in sorted(groups[g], key=lambda x: x[0])), ""]
    out.append(f"[{version}]: {url}/releases/tag/v{version}")
    if left_out:
        out += ["", "<!-- Left out as maintenance. Add back anything a user of the release would notice:"]
        out += [f"  {x}" for x in left_out] + ["-->"]
    print("\n".join(out))
    return 0


def cmd_changelog_entry(args):
    version = args.version[1:] if args.version.startswith("v") else args.version
    heading = re.compile(r"^## \[?" + re.escape(version) + r"\]? - \d{4}-\d{2}-\d{2}")
    lines, inside = [], False
    with open(args.file, encoding="utf-8") as f:
        for line in f:
            if line.startswith("## ") or re.match(r"^\[[^\]]+\]: ", line):
                if inside:
                    break
                inside = bool(heading.match(line))
                continue
            if inside:
                lines.append(line.rstrip("\n"))
    if not inside:
        print(f"ADLC: {args.file} has no '## {version} - YYYY-MM-DD' entry. Write it before tagging.", file=sys.stderr)
        return 1
    print("\n".join(lines).strip())
    return 0


# Files `sync` writes into a repo, as (path in the repo, source in the ADLC repo).
# Managed files belong to the ADLC: every sync overwrites them, and the drift job in adlc.yml
# fails a PR whose copy differs from the pinned release. A source of None is the version record.
MANAGED = (
    (".adlc/version", None),
    (".adlc/scripts/adlc.py", "scripts/adlc.py"),
    (".githooks/pre-commit", "templates/git-hooks/pre-commit"),
    (".github/workflows/adlc.yml", "templates/github/workflows/adlc.yml"),
    (".github/workflows/adlc-review.yml", "templates/github/workflows/adlc-review.yml"),
    (".github/workflows/adlc-pr-title.yml", "templates/github/workflows/adlc-pr-title.yml"),
    (".github/workflows/adlc-dependabot.yml", "templates/github/workflows/adlc-dependabot.yml"),
    (".github/pull_request_template.md", "templates/pull_request_template.md"),
)
# Managed only in repos that ship releases: sync --releases adds it, and later syncs keep it.
MANAGED_RELEASES = ((".github/workflows/adlc-release.yml", "templates/github/workflows/adlc-release.yml"),)
# Repo-owned files start from a template. Sync adds them only when missing and never checks them.
SEEDS = (
    ("AGENTS.md", "templates/AGENTS.md"),
    ("REVIEW.md", "templates/REVIEW.md"),
    (".adlc/tiers", "templates/adlc/tiers"),
    (".adlc/protected", "templates/adlc/protected"),
    (".adlc/install", "templates/adlc/install"),
    (".adlc/fast-check", "templates/adlc/fast-check"),
    (".adlc/full-test", "templates/adlc/full-test"),
    (".adlc/retire-log.md", "templates/adlc/retire-log.md"),
    (".editorconfig", "templates/editorconfig"),
    (".github/dependabot.yml", "templates/github/dependabot.yml"),
)
SEEDS_RELEASES = (("CHANGELOG.md", "templates/CHANGELOG.md"),)
VERSION_TOKEN = b"{{ADLC_VERSION}}"
DRIFT_WORKFLOW = ".github/workflows/adlc.yml"
MANIFEST_BEGIN = "# BEGIN manifest"
MANIFEST_END = "# END manifest"


def adlc_root():
    """The ADLC checkout this script is in. A repo's .adlc/scripts copy has no templates to sync."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isfile(os.path.join(root, ".claude-plugin", "plugin.json")):
        sys.exit("adlc.py: run this with scripts/adlc.py in an ADLC checkout, not a repo's .adlc/scripts copy.")
    return root


def adlc_version(root):
    with open(os.path.join(root, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        return json.load(f)["version"]


def render(root, source, version):
    """The bytes and executable bit `sync` writes for a source. Templates get the version filled in."""
    if source is None:
        return f"{version}\n".encode(), False
    path = os.path.join(root, source)
    with open(path, "rb") as f:
        data = f.read()
    if source.startswith("templates/"):
        data = data.replace(VERSION_TOKEN, version.encode())
    return data, bool(os.stat(path).st_mode & 0o100)


def manifest_lines(root, version):
    """The shell lines between the markers in the drift job: version and `sha256 path [optional]` rows."""
    rows = [(p, s, "") for p, s in MANAGED] + [(p, s, " optional") for p, s in MANAGED_RELEASES]
    lines = [f"version={version}", "manifest='"]
    for path, source, flag in rows:
        lines.append(f"{hashlib.sha256(render(root, source, version)[0]).hexdigest()} {path}{flag}")
    return lines + ["'"]


def cmd_manifest(args):
    root = adlc_root()
    lines = manifest_lines(root, adlc_version(root))
    if not (args.write or args.check):
        print("\n".join(lines))
        return 0
    path = os.path.join(root, DRIFT_WORKFLOW)
    with open(path, encoding="utf-8") as f:
        text = f.read().split("\n")
    begin = next((i for i, line in enumerate(text) if line.strip().startswith(MANIFEST_BEGIN)), None)
    end = next((i for i, line in enumerate(text) if line.strip().startswith(MANIFEST_END)), None)
    if begin is None or end is None or end < begin:
        sys.exit(f"adlc.py: {DRIFT_WORKFLOW} has no '{MANIFEST_BEGIN}' ... '{MANIFEST_END}' block.")
    indent = text[begin][: len(text[begin]) - len(text[begin].lstrip())]
    new = [indent + line for line in lines]
    if text[begin + 1 : end] == new:
        return 0
    if args.check:
        print(f"ADLC: the manifest in {DRIFT_WORKFLOW} is out of date. Run: python3 scripts/adlc.py manifest --write",
              file=sys.stderr)
        return 1
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(text[: begin + 1] + new + text[end:]))
    return 0


def check_release_checkout(root, version):
    """Refuse a git checkout that is not exactly at tag vVERSION, so a repo never gets unreleased files."""
    top = subprocess.run(["git", "-C", root, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode != 0 or os.path.realpath(top.stdout.strip()) != os.path.realpath(root):
        return
    tag = subprocess.run(["git", "-C", root, "describe", "--exact-match", "--tags", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", root, "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True).stdout.strip()
    if tag != f"v{version}" or dirty:
        sys.exit(f"adlc.py: {root} is not a clean checkout of release tag v{version}. "
                 "Sync from a release: git checkout vX.Y.Z (see docs/sync.md).")


def cmd_sync(args):
    root = adlc_root()
    version = adlc_version(root)
    check_release_checkout(root, version)
    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        sys.exit(f"adlc.py: {target} is not a directory.")
    releases = args.releases or os.path.exists(os.path.join(target, MANAGED_RELEASES[0][0]))
    managed = MANAGED + (MANAGED_RELEASES if releases else ())
    seeds = SEEDS + (SEEDS_RELEASES if releases else ())
    before = "none"
    if os.path.isfile(os.path.join(target, ".adlc", "version")):
        with open(os.path.join(target, ".adlc", "version"), encoding="utf-8") as f:
            before = f.read().strip()
    changes = []
    for (path, source), owned in [(m, False) for m in managed] + [(s, True) for s in seeds]:
        dest = os.path.join(target, path)
        exists = os.path.isfile(dest)
        if owned and exists:
            continue
        data, executable = render(root, source, version)
        if exists:
            with open(dest, "rb") as f:
                same = f.read() == data
            if same and bool(os.stat(dest).st_mode & 0o100) == executable:
                continue
        changes.append(f"{'update' if exists else 'add'} {path}")
        if args.check:
            continue
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        os.chmod(dest, 0o755 if executable else 0o644)
    for change in changes:
        print(("would " if args.check else "") + change)
    if args.check:
        return 1 if changes else 0
    if os.path.exists(os.path.join(target, ".git")):
        hooks = subprocess.run(["git", "-C", target, "config", "core.hooksPath", ".githooks"], capture_output=True)
        if hooks.returncode != 0:
            print("ADLC: could not set core.hooksPath; run: git config core.hooksPath .githooks", file=sys.stderr)
    print(f"ADLC {before} -> {version}: {len(changes)} file(s) changed.", file=sys.stderr)
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
    pc = sub.add_parser("protected-changes")
    pc.add_argument("--base", required=True)
    pc.add_argument("--head", required=True)
    pc.add_argument("--list", default=".adlc/protected")
    r = sub.add_parser("review-rounds")
    r.add_argument("--reviewers", required=True)
    pt = sub.add_parser("pr-title")
    pt.add_argument("title")
    cd = sub.add_parser("changelog-draft")
    cd.add_argument("--current", required=True)
    cd.add_argument("--repo", required=True)
    cd.add_argument("--date")
    ce = sub.add_parser("changelog-entry")
    ce.add_argument("version")
    ce.add_argument("--file", default="CHANGELOG.md")
    sy = sub.add_parser("sync")
    sy.add_argument("target")
    sy.add_argument("--releases", action="store_true")
    sy.add_argument("--check", action="store_true")
    m = sub.add_parser("manifest")
    mode = m.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = p.parse_args()
    return {
        "tier": cmd_tier,
        "check-protected": cmd_check_protected,
        "protected-changes": cmd_protected_changes,
        "review-rounds": cmd_review_rounds,
        "pr-title": cmd_pr_title,
        "changelog-draft": cmd_changelog_draft,
        "changelog-entry": cmd_changelog_entry,
        "sync": cmd_sync,
        "manifest": cmd_manifest,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
