import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "adlc.py")


def run(args, stdin="", cwd=None, env=None):
    p = subprocess.run(
        [sys.executable, SCRIPT, *args], input=stdin, capture_output=True, text=True, cwd=cwd,
        env={**os.environ, **(env or {})},
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


class Tier(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.map = os.path.join(self.d, "tiers")
        with open(self.map, "w") as f:
            f.write("# comment\nT1 docs/**\nT1 **/*.md\nT1 **/*.css\nT3 .github/workflows/**\nT3 src/grading/**\n")

    def tier(self, *paths):
        return run(["tier", "--map", self.map, *paths])[1]

    def test_unmatched_is_t2(self):
        self.assertEqual(self.tier("src/app.js"), "T2")

    def test_docs_and_css_are_t1(self):
        self.assertEqual(self.tier("docs/a/b.txt", "README.md", "web/site.css"), "T1")

    def test_highest_tier_wins(self):
        self.assertEqual(self.tier("README.md", "src/app.js", "src/grading/score.js"), "T3")

    def test_md_inside_t3_dir_is_t3(self):
        self.assertEqual(self.tier("src/grading/notes.md"), "T3")

    def test_dot_directory_and_dot_slash(self):
        self.assertEqual(self.tier("./.github/workflows/ci.yml"), "T3")

    def test_star_does_not_cross_directories(self):
        with open(self.map, "w") as f:
            f.write("T3 src/*.js\n")
        self.assertEqual(self.tier("src/a/b.js"), "T2")
        self.assertEqual(self.tier("src/b.js"), "T3")

    def test_stdin_and_empty(self):
        self.assertEqual(run(["tier", "--map", self.map], stdin="README.md\nsrc/x.py\n")[1], "T2")
        self.assertEqual(run(["tier", "--map", self.map], stdin="")[1], "T1")

    def test_missing_map_means_t2(self):
        self.assertEqual(run(["tier", "--map", os.path.join(self.d, "none"), "a.md"])[1], "T2")

    def test_bad_line_fails(self):
        with open(self.map, "w") as f:
            f.write("T9 x\n")
        self.assertNotEqual(run(["tier", "--map", self.map, "x"])[0], 0)


class Protected(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, ".adlc"))
        with open(os.path.join(self.d, ".adlc", "protected"), "w") as f:
            f.write("tests/regression/**\n")

    def hook(self, file_path):
        event = {"cwd": self.d, "tool_name": "Edit", "tool_input": {"file_path": file_path}}
        return run(["check-protected"], stdin=json.dumps(event), cwd=self.d)

    def test_blocks_protected_absolute_path(self):
        code, _, err = self.hook(os.path.join(self.d, "tests/regression/bug1.test.js"))
        self.assertEqual(code, 2)
        self.assertIn("protected", err)

    def test_allows_other_paths(self):
        self.assertEqual(self.hook("src/app.js")[0], 0)

    def test_uses_project_dir_from_a_subdirectory(self):
        sub = os.path.join(self.d, "tests")
        os.makedirs(sub, exist_ok=True)
        event = {"cwd": sub, "tool_input": {"file_path": "regression/bug2.test.js"}}
        code = run(["check-protected"], stdin=json.dumps(event), cwd="/", env={"CLAUDE_PROJECT_DIR": self.d})[0]
        self.assertEqual(code, 2)

    def test_ignores_events_without_a_path(self):
        self.assertEqual(run(["check-protected"], stdin=json.dumps({"tool_input": {}}), cwd=self.d)[0], 0)


class ReviewRounds(unittest.TestCase):
    def test_counts_only_listed_reviewers_and_real_states(self):
        reviews = [
            {"user": {"login": "claude[bot]"}, "state": "COMMENTED"},
            {"user": {"login": "Claude[bot]"}, "state": "CHANGES_REQUESTED"},
            {"user": {"login": "claude[bot]"}, "state": "PENDING"},
            {"user": {"login": "anandfrancis93"}, "state": "APPROVED"},
            {"user": {"login": "codex-bot"}, "state": "COMMENTED"},
        ]
        out = run(["review-rounds", "--reviewers", "claude[bot],codex-bot"], stdin=json.dumps(reviews))[1]
        self.assertEqual(out, "3")


if __name__ == "__main__":
    unittest.main()


class PrTitle(unittest.TestCase):
    def ok(self, title):
        return run(["pr-title", title])[0] == 0

    def test_valid_titles(self):
        for t in ("feat: add login", "fix(api): reject empty names", "feat!: drop node 18",
                  "refactor(core)!: split parser", "Docs: fix typo", "revert: undo x"):
            self.assertTrue(self.ok(t), t)

    def test_invalid_titles(self):
        for t in ("Add login", "feat:add login", "feat : add login", "feature: add login",
                  "fix(): empty scope", "feat: ", "fix(api) reject"):
            self.assertFalse(self.ok(t), t)


class ChangelogDraft(unittest.TestCase):
    def draft(self, commits, current="0.1.0"):
        log = "".join(f"{sha}\x1f{subject}\x1f{body}\x1e\n" for sha, subject, body in commits)
        return run(["changelog-draft", "--current", current, "--repo", "o/n", "--date", "2026-10-22"], stdin=log)

    def test_feat_bumps_minor_and_groups(self):
        code, out, _ = self.draft([
            ("bbb2222", "fix: handle empty map (#4)", ""),
            ("aaa1111", "feat(cli): add tier explain", ""),
            ("ccc3333", "docs: reword readme", ""),
        ])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("## [0.2.0] - 2026-10-22"))
        self.assertIn("### Added\n\n- Add tier explain ([`aaa1111`](https://github.com/o/n/commit/aaa1111))", out)
        self.assertIn("- Handle empty map ([`bbb2222`](https://github.com/o/n/commit/bbb2222)) "
                      "([#4](https://github.com/o/n/pull/4))", out)
        self.assertLess(out.index("### Added"), out.index("### Fixed"))
        self.assertIn("ccc3333 docs: reword readme", out.split("<!--")[1])

    def test_breaking_bumps_major_and_comes_first(self):
        code, out, _ = self.draft([
            ("aaa1111", "perf: faster tiering", ""),
            ("bbb2222", "feat: new map format", "Body.\n\nBREAKING CHANGE: old maps fail"),
        ], current="1.4.2")
        self.assertTrue(out.startswith("## [2.0.0]"))
        changed = out.split("### Changed\n\n")[1].splitlines()
        self.assertTrue(changed[0].startswith("- **Breaking:** new map format"))
        self.assertTrue(changed[1].startswith("- Faster tiering"))

    def test_breaking_before_1_0_bumps_minor(self):
        out = self.draft([("a1", "feat!: new map format", "")], current="0.3.1")[1]
        self.assertTrue(out.startswith("## [0.4.0]"))
        self.assertIn("- **Breaking:** new map format", out)

    def test_fix_only_bumps_patch(self):
        self.assertTrue(self.draft([("a1", "fix: x", "")], current="v1.2.3")[1].startswith("## [1.2.4]"))

    def test_nothing_user_facing_exits_3(self):
        self.assertEqual(self.draft([("a1", "ci: cache deps", "")])[0], 3)

    def test_bad_current_version_fails(self):
        self.assertNotEqual(self.draft([("a1", "fix: x", "")], current="1.2")[0], 0)


class ChangelogEntry(unittest.TestCase):
    def setUp(self):
        self.f = os.path.join(tempfile.mkdtemp(), "CHANGELOG.md")
        with open(self.f, "w") as fh:
            fh.write("# Changelog\n\n## [0.2.0] - 2026-10-22\n\n### Added\n\n- Add x ([`a1`](u))\n\n"
                     "## [0.1.0] - 2026-10-21\n\n_First release._\n\n[0.2.0]: https://x/v0.2.0\n[0.1.0]: https://x/v0.1.0\n")

    def test_prints_entry_without_heading_or_links(self):
        code, out, _ = run(["changelog-entry", "v0.2.0", "--file", self.f])
        self.assertEqual((code, out), (0, "### Added\n\n- Add x ([`a1`](u))"))
        self.assertEqual(run(["changelog-entry", "0.1.0", "--file", self.f])[1], "_First release._")

    def test_missing_entry_fails(self):
        self.assertEqual(run(["changelog-entry", "0.3.0", "--file", self.f])[0], 1)
