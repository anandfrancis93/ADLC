import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SCRIPT = os.path.join(ROOT, "scripts", "adlc.py")


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


class ProtectedChanges(unittest.TestCase):
    LIST = ".adlc/protected"

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.git("init", "-q", "-b", "main")
        self.base = self.commit({"src/app.py": "x = 1\n", "tests/regression/bug1.py": "assert x\n",
                                 self.LIST: "tests/regression/bug1.py\n"})

    def git(self, *args):
        p = subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", *args],
            cwd=self.d, capture_output=True, text=True, check=True,
        )
        return p.stdout.strip()

    def commit(self, files):
        for path, text in files.items():
            full = os.path.join(self.d, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w") as f:
                f.write(text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "change")
        return self.git("rev-parse", "HEAD")

    def check(self):
        return run(["protected-changes", "--base", self.base, "--head", "HEAD"], cwd=self.d)

    def test_other_changes_pass(self):
        self.commit({"src/app.py": "x = 2\n"})
        self.assertEqual(self.check()[0], 0)

    def test_editing_a_path_protected_on_the_base_fails(self):
        self.commit({"tests/regression/bug1.py": "pass\n"})
        code, _, err = self.check()
        self.assertEqual(code, 1)
        self.assertIn("tests/regression/bug1.py", err)

    def test_failing_test_then_fix_passes(self):
        self.commit({"tests/regression/bug2.py": "assert fixed\n",
                     self.LIST: "tests/regression/bug1.py\ntests/regression/bug2.py\n"})
        self.commit({"src/app.py": "fixed = True\n"})
        self.assertEqual(self.check()[0], 0)

    def test_test_protected_earlier_in_the_pr_is_covered(self):
        self.commit({"tests/regression/bug2.py": "assert fixed\n",
                     self.LIST: "tests/regression/bug1.py\ntests/regression/bug2.py\n"})
        self.commit({"src/app.py": "fixed = True\n", "tests/regression/bug2.py": "pass\n"})
        code, _, err = self.check()
        self.assertEqual(code, 1)
        self.assertIn("bug2.py", err)

    def test_removing_a_line_alone_passes(self):
        self.commit({self.LIST: ""})
        self.assertEqual(self.check()[0], 0)

    def test_unprotecting_as_the_last_commit_passes(self):
        self.commit({"tests/regression/bug2.py": "assert fixed\n",
                     self.LIST: "tests/regression/bug1.py\ntests/regression/bug2.py\n"})
        self.commit({"src/app.py": "fixed = True\n"})
        self.commit({self.LIST: "tests/regression/bug1.py\n"})
        self.assertEqual(self.check()[0], 0)

    def test_changes_after_removing_a_line_fail(self):
        self.commit({self.LIST: ""})
        self.commit({"tests/regression/bug1.py": "pass\n"})
        code, _, err = self.check()
        self.assertEqual(code, 1)
        self.assertIn("after", err)

    def test_removing_a_line_with_other_changes_in_one_commit_fails(self):
        self.commit({self.LIST: "", "src/app.py": "x = 2\n"})
        code, _, err = self.check()
        self.assertEqual(code, 1)
        self.assertIn("src/app.py", err)

    def test_hand_edit_in_a_merge_of_the_base_fails(self):
        self.git("checkout", "-q", "-b", "pr")
        self.commit({"src/app.py": "x = 2\n"})
        self.git("checkout", "-q", "main")
        self.base = self.commit({"src/other.py": "y = 1\n"})
        self.git("checkout", "-q", "pr")
        self.git("merge", "-q", "--no-ff", "--no-commit", "main")
        self.commit({"tests/regression/bug1.py": "pass\n"})
        code, _, err = self.check()
        self.assertEqual(code, 1)
        self.assertIn("bug1.py", err)

    def test_merging_the_base_passes_even_when_the_base_unprotected_a_test(self):
        self.git("checkout", "-q", "-b", "pr")
        self.commit({"src/app.py": "x = 2\n"})
        self.git("checkout", "-q", "main")
        self.commit({self.LIST: ""})
        self.base = self.commit({"tests/regression/bug1.py": "pass\n"})
        self.git("checkout", "-q", "pr")
        self.git("merge", "-q", "--no-edit", "main")
        self.commit({"src/app.py": "x = 3\n"})
        self.assertEqual(self.check()[0], 0)

    def test_merge_of_another_branch_is_checked_as_one_commit(self):
        self.base = self.commit({"tests/regression/bug3.py": "a\nb\nc\n"})
        self.git("checkout", "-q", "-b", "side")
        self.commit({"tests/regression/bug3.py": "a\nb\nweakened\n"})
        self.git("checkout", "-q", "-b", "pr", self.base)
        self.commit({"tests/regression/bug3.py": "tightened\nb\nc\n",
                     self.LIST: "tests/regression/bug1.py\ntests/regression/bug3.py\n"})
        self.git("merge", "-q", "--no-edit", "side")
        code, _, err = self.check()
        self.assertEqual(code, 1)
        self.assertIn("bug3.py", err)

    def test_changes_after_a_merge_that_removes_lines_fail(self):
        self.git("checkout", "-q", "-b", "pr")
        self.git("checkout", "-q", "main")
        self.base = self.commit({"src/other.py": "y = 1\n"})
        self.git("checkout", "-q", "pr")
        self.git("merge", "-q", "--no-ff", "--no-commit", "main")
        self.commit({self.LIST: ""})
        self.commit({"tests/regression/bug1.py": "pass\n"})
        code, _, err = self.check()
        self.assertEqual(code, 1)
        self.assertIn("after", err)

    def test_no_list_passes(self):
        self.git("rm", "-q", self.LIST)
        self.git("commit", "-q", "-m", "drop list")
        self.base = self.git("rev-parse", "HEAD")
        self.commit({"tests/regression/bug1.py": "pass\n"})
        self.assertEqual(self.check()[0], 0)


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


class T3Approved(unittest.TestCase):
    def check(self, reviews=(), events=(), owner="Anand", since="2026-10-22T05:00:00Z"):
        d = tempfile.mkdtemp()
        files = {}
        for name, data in (("reviews", reviews), ("events", events)):
            files[name] = os.path.join(d, name + ".json")
            with open(files[name], "w") as f:
                json.dump(list(data), f)
        code, out, err = run(["t3-status", "--tier", "T3", "--owner", owner, "--head", "h2", "--since", since,
                              "--reviews", files["reviews"], "--events", files["events"]])
        self.assertEqual(code, 0, err)
        return 0 if json.loads(out)["state"] == "success" else 1

    def label(self, event, login, name="adlc:t3-approved", at="2026-10-22T05:10:00Z"):
        return {"event": event, "actor": {"login": login}, "label": {"name": name}, "created_at": at}

    def test_owner_review_of_the_latest_commit_passes(self):
        self.assertEqual(self.check([{"user": {"login": "anand"}, "state": "APPROVED", "commit_id": "h2"}]), 0)
        self.assertEqual(self.check([{"user": {"login": "anand"}, "state": "APPROVED", "commit_id": "h1"}]), 1)
        self.assertEqual(self.check([{"user": {"login": "other"}, "state": "APPROVED", "commit_id": "h2"}]), 1)

    def test_label_counts_only_when_the_owner_added_it_last(self):
        self.assertEqual(self.check(events=[self.label("labeled", "anand")]), 0)
        self.assertEqual(self.check(events=[self.label("labeled", "other")]), 1)
        self.assertEqual(self.check(events=[self.label("labeled", "anand"), self.label("unlabeled", "bot")]), 1)
        self.assertEqual(self.check(events=[self.label("labeled", "anand"), self.label("unlabeled", "bot"),
                                            self.label("labeled", "other")]), 1)
        self.assertEqual(self.check(events=[self.label("labeled", "anand"), self.label("labeled", "x", "adlc:T3"),
                                            {"event": "committed"}]), 0)
        self.assertEqual(self.check(events=[self.label("labeled", "anand", "approved")]), 1)

    def test_events_count_in_time_order(self):
        added = {**self.label("labeled", "anand", at="2026-10-22T05:10:00Z"), "id": 1}
        removed = {**self.label("unlabeled", "bot", at="2026-10-22T05:11:00Z"), "id": 2}
        self.assertEqual(self.check(events=[removed, added]), 1)

    def test_label_from_before_the_commit_does_not_count(self):
        self.assertEqual(self.check(events=[self.label("labeled", "anand", at="2026-10-22T04:59:59Z")]), 1)
        self.assertEqual(self.check(events=[self.label("labeled", "anand", at="2026-10-22T05:00:00Z")]), 1)
        self.assertEqual(self.check(events=[self.label("labeled", "anand")], since=""), 1)

    def test_label_from_before_a_force_push_does_not_count(self):
        """A force push back to an earlier commit keeps that commit's old check suites."""
        pushed = {"event": "head_ref_force_pushed", "actor": {"login": "anand"}, "created_at": "2026-10-22T05:20:00Z"}
        self.assertEqual(self.check(events=[self.label("labeled", "anand"), pushed]), 1)
        self.assertEqual(self.check(events=[self.label("labeled", "anand", at="2026-10-22T05:20:00Z"), pushed]), 1)
        self.assertEqual(self.check(events=[pushed, self.label("labeled", "anand", at="2026-10-22T05:30:00Z")]), 0)
        newer = {**pushed, "created_at": "2026-10-22T05:40:00Z"}
        self.assertEqual(self.check(events=[pushed, self.label("labeled", "anand", at="2026-10-22T05:30:00Z"), newer]), 1)
        older = {**pushed, "created_at": "2026-10-22T04:00:00Z"}
        self.assertEqual(self.check(events=[older, pushed, self.label("labeled", "anand", at="2026-10-22T05:30:00Z")]), 0)
        self.assertEqual(self.check(events=[older, self.label("labeled", "anand", at="2026-10-22T04:30:00Z")]), 1)

    def test_unset_owner_fails(self):
        self.assertEqual(self.check([{"user": None, "state": "APPROVED", "commit_id": "h2"}], owner=""), 1)
        self.assertEqual(self.check(events=[{**self.label("labeled", "x"), "actor": None}], owner=" "), 1)

    def test_no_approval_fails(self):
        self.assertEqual(self.check(), 1)


class T3Status(unittest.TestCase):
    def status(self, tier, owner="anand", events=None):
        args = ["t3-status", "--tier", tier, "--owner", owner, "--head", "h2", "--since", "2026-10-22T05:00:00Z"]
        if events is not None:
            d = tempfile.mkdtemp()
            for name, text in (("reviews", "[]"), ("events", events)):
                with open(os.path.join(d, name), "w") as f:
                    f.write(text)
            args += ["--reviews", os.path.join(d, "reviews"), "--events", os.path.join(d, "events")]
        return run(args)

    def test_t3_status_reports_each_tier(self):
        for tier in ("T1", "T2"):
            code, out, err = self.status(tier)
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(out)["state"], "success", tier)
        label = {"event": "labeled", "actor": {"login": "anand"}, "label": {"name": "adlc:t3-approved"},
                 "created_at": "2026-10-22T05:10:00Z"}
        for events, state in (("[]", "pending"), (json.dumps([label]), "success")):
            code, out, err = self.status("T3", events=events)
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(out)["state"], state, events)
        long = "a" * 39
        for tier, owner, events in (("T1", long, None), ("T3", long, "[]"), ("T3", long, json.dumps([label])),
                                    ("T3", "", "[]")):
            code, out, err = self.status(tier, owner, events)
            status = json.loads(out)
            self.assertEqual(set(status), {"state", "description"})
            # The GitHub statuses API takes a description of at most 140 characters.
            self.assertLessEqual(len(status["description"]), 140, status)

    def test_t3_status_fails_on_a_bad_file(self):
        """An error must fail the job, not read as an approval that is still to come."""
        self.assertEqual(self.status("T3", events="[]")[0], 0)
        code, out, err = self.status("T3", events="not json")
        self.assertNotEqual(code, 0)
        self.assertEqual(out, "")


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


def git_in(d, *args):
    p = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false",
         "-c", "tag.gpgsign=false", *args],
        cwd=d, capture_output=True, text=True, check=True,
    )
    return p.stdout.strip()


def load_adlc():
    spec = importlib.util.spec_from_file_location("adlc", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SyncedRepo(unittest.TestCase):
    """A copy of this ADLC checkout, tagged as its release, and an empty repo to sync into."""

    def setUp(self):
        tmp = tempfile.mkdtemp()
        self.adlc = os.path.join(tmp, "ADLC")
        for d in ("scripts", "templates", ".claude-plugin", ".github"):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(self.adlc, d))
        shutil.copy(os.path.join(ROOT, "CHANGELOG.md"), self.adlc)
        with open(os.path.join(ROOT, ".claude-plugin", "plugin.json")) as f:
            self.version = json.load(f)["version"]
        git_in(self.adlc, "init", "-q")
        git_in(self.adlc, "add", "-A")
        git_in(self.adlc, "commit", "-q", "-m", "release")
        git_in(self.adlc, "tag", f"v{self.version}")
        self.repo = os.path.join(tmp, "repo")
        os.makedirs(self.repo)
        git_in(self.repo, "init", "-q")

    def sync(self, *args, script=None):
        p = subprocess.run(
            [sys.executable, script or os.path.join(self.adlc, "scripts", "adlc.py"), "sync", self.repo, *args],
            capture_output=True, text=True,
        )
        return p.returncode, p.stdout, p.stderr

    def path(self, rel):
        return os.path.join(self.repo, rel)

    def read(self, rel):
        with open(self.path(rel)) as f:
            return f.read()

    def write(self, rel, text):
        with open(self.path(rel), "w") as f:
            f.write(text)


class Sync(SyncedRepo):
    def test_adds_managed_and_repo_owned_files(self):
        code, out, _ = self.sync()
        self.assertEqual(code, 0)
        self.assertEqual(self.read(".adlc/version"), f"{self.version}\n")
        caller = self.read(".github/workflows/adlc.yml")
        self.assertIn(f"anandfrancis93/ADLC/.github/workflows/adlc.yml@v{self.version}\n", caller)
        self.assertNotIn("ADLC_VERSION}}", caller)
        self.assertIn("add AGENTS.md", out)
        self.assertTrue(os.access(self.path(".githooks/pre-commit"), os.X_OK))
        self.assertTrue(os.access(self.path(".adlc/install"), os.X_OK))
        self.assertEqual(git_in(self.repo, "config", "core.hooksPath"), ".githooks")
        self.assertFalse(os.path.exists(self.path(".github/workflows/adlc-release.yml")))
        self.assertFalse(os.path.exists(self.path("CHANGELOG.md")))

    def test_restores_managed_files_and_keeps_repo_owned_ones(self):
        self.sync()
        self.write("AGENTS.md", "# mine\n")
        self.write(".adlc/scripts/adlc.py", "edited\n")
        code, out, _ = self.sync()
        self.assertEqual((code, out), (0, "update .adlc/scripts/adlc.py\n"))
        self.assertEqual(self.read("AGENTS.md"), "# mine\n")
        with open(SCRIPT) as f:
            self.assertEqual(self.read(".adlc/scripts/adlc.py"), f.read())

    def test_check_lists_changes_without_writing(self):
        self.sync()
        self.assertEqual(self.sync("--check")[0], 0)
        self.write(".githooks/pre-commit", "edited\n")
        code, out, _ = self.sync("--check")
        self.assertEqual((code, out), (1, "would update .githooks/pre-commit\n"))
        self.assertEqual(self.read(".githooks/pre-commit"), "edited\n")

    def test_releases_flag_adds_release_files_and_later_syncs_keep_them(self):
        self.sync("--releases")
        self.assertIn("# Changelog", self.read("CHANGELOG.md"))
        self.write(".github/workflows/adlc-release.yml", "edited\n")
        self.sync()
        self.assertIn(f"adlc-release.yml@v{self.version}", self.read(".github/workflows/adlc-release.yml"))

    def test_refuses_a_checkout_that_is_not_the_release(self):
        with open(os.path.join(self.adlc, "templates", "REVIEW.md"), "a") as f:
            f.write("unreleased\n")
        code, _, err = self.sync()
        self.assertNotEqual(code, 0)
        self.assertIn("release tag", err)
        git_in(self.adlc, "commit", "-q", "-am", "unreleased")
        self.assertNotEqual(self.sync()[0], 0)
        self.assertFalse(os.path.exists(self.path("REVIEW.md")))

    def test_refuses_a_repos_own_copy(self):
        self.sync()
        code, _, err = self.sync(script=self.path(".adlc/scripts/adlc.py"))
        self.assertNotEqual(code, 0)
        self.assertIn("ADLC checkout", err)


class Drift(SyncedRepo):
    """Runs the shell script of the drift job in this repo's adlc.yml, as GitHub runs it."""

    def setUp(self):
        super().setUp()
        with open(os.path.join(ROOT, ".github", "workflows", "adlc.yml")) as f:
            lines = f.read().split("\n")
        begin = next(i for i, line in enumerate(lines) if line.strip().startswith("# BEGIN manifest"))
        indent = lines[begin][: len(lines[begin]) - len(lines[begin].lstrip())]
        script = []
        for line in lines[begin:]:
            if line.strip() and not line.startswith(indent):
                break
            script.append(line[len(indent):])
        self.script = "\n".join(script)
        self.sync()

    def drift(self):
        p = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", self.script],
                           cwd=self.repo, capture_output=True, text=True)
        return p.returncode, p.stdout

    def test_synced_repo_passes(self):
        self.assertEqual(self.drift(), (0, ""))

    def test_edited_file_fails(self):
        self.write(".github/workflows/adlc.yml", self.read(".github/workflows/adlc.yml").replace("@v", "@main#"))
        code, out = self.drift()
        self.assertEqual(code, 1)
        self.assertIn("::error file=.github/workflows/adlc.yml::", out)

    def test_other_version_fails(self):
        self.write(".adlc/version", "0.0.1\n")
        self.assertEqual(self.drift()[0], 1)

    def test_missing_file_fails(self):
        os.remove(self.path(".github/pull_request_template.md"))
        code, out = self.drift()
        self.assertEqual(code, 1)
        self.assertIn("missing", out)

    def test_release_workflow_is_checked_when_present(self):
        self.sync("--releases")
        self.assertEqual(self.drift()[0], 0)
        self.write(".github/workflows/adlc-release.yml", "edited\n")
        self.assertEqual(self.drift()[0], 1)

    def test_repo_owned_files_may_change(self):
        self.write("AGENTS.md", "# mine\n")
        self.write(".adlc/tiers", "T3 **\n")
        self.assertEqual(self.drift()[0], 0)


FAKE_GH = r"""
import json, os, subprocess, sys
state = os.environ["FAKE_GH_STATE"]
args = sys.argv[1:]
def opt(name):
    return args[args.index(name) + 1]
if args[:2] == ["repo", "list"]:
    print(open(os.path.join(state, "repos.json")).read())
elif args[0] == "api":
    repo, path = args[1].split("/contents/")
    repo = repo[len("repos/"):]
    if repo == "o/broken":
        sys.exit("gh: Server Error (HTTP 500)")
    p = subprocess.run(["git", "--git-dir", os.path.join(state, "remotes", repo), "show", "HEAD:" + path],
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit("gh: Not Found (HTTP 404)")
    sys.stdout.write(p.stdout)
elif args[:2] == ["pr", "list"]:
    open_prs = os.path.join(state, "open", opt("-R").replace("/", "_"))
    print(open(open_prs).read() if os.path.exists(open_prs) else "[]")
elif args[:2] == ["pr", "create"]:
    with open(os.path.join(state, "created.jsonl"), "a") as f:
        f.write(json.dumps({"repo": opt("-R"), "head": opt("--head"), "base": opt("--base"),
                            "title": opt("--title"), "body": open(opt("--body-file")).read()}) + "\n")
    print("https://github.com/" + opt("-R") + "/pull/1")
else:
    sys.exit("fake gh: unexpected " + " ".join(args))
"""


class SyncRepos(SyncedRepo):
    """Runs sync-repos against a fake gh and local bare repos standing in for github.com."""

    def setUp(self):
        super().setUp()
        self.state = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.state, "open"))
        bin_dir = os.path.join(self.state, "bin")
        os.makedirs(bin_dir)
        with open(os.path.join(bin_dir, "gh"), "w") as f:
            f.write(f"#!{sys.executable}\n{FAKE_GH}")
        os.chmod(os.path.join(bin_dir, "gh"), 0o755)
        repos = {"o/behind": {".adlc/version": "0.0.1\n", ".adlc/tiers": "T1 docs/**\n", "AGENTS.md": "# mine\n"},
                 "o/current": {".adlc/version": f"{self.version}\n"},
                 "o/copied": {".adlc/tiers": "T1 docs/**\n"},
                 "o/other": {"README.md": "hi\n"},
                 "o/broken": {"README.md": "hi\n"},
                 "o/ADLC": {".adlc/version": "0.0.1\n"}}
        for name, files in repos.items():
            self.remote(name, files)
        with open(os.path.join(self.state, "repos.json"), "w") as f:
            json.dump([{"nameWithOwner": n, "defaultBranchRef": {"name": "main"}} for n in repos], f)
        self.env = {
            "PATH": bin_dir + os.pathsep + os.environ["PATH"], "GH_TOKEN": "t", "FAKE_GH_STATE": self.state,
            "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": f"url.file://{self.state}/remotes/.insteadOf",
            "GIT_CONFIG_VALUE_0": "https://github.com/", "GITHUB_STEP_SUMMARY": os.path.join(self.state, "summary"),
        }

    def remote(self, name, files):
        work = tempfile.mkdtemp()
        git_in(work, "init", "-q", "-b", "main")
        for path, text in files.items():
            os.makedirs(os.path.join(work, os.path.dirname(path)), exist_ok=True)
            with open(os.path.join(work, path), "w") as f:
                f.write(text)
        git_in(work, "add", "-A")
        git_in(work, "commit", "-q", "-m", "init")
        bare = os.path.join(self.state, "remotes", name)
        os.makedirs(os.path.dirname(bare), exist_ok=True)
        git_in(work, "clone", "-q", "--bare", work, bare)

    def sync_repos(self, *args):
        p = subprocess.run([sys.executable, os.path.join(self.adlc, "scripts", "adlc.py"), "sync-repos",
                            "--owner", "o", "--skip", "o/ADLC", *args],
                           capture_output=True, text=True, env={**os.environ, **self.env})
        return p.returncode, p.stdout, p.stderr

    def created(self):
        path = os.path.join(self.state, "created.jsonl")
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return [json.loads(line) for line in f]

    def remote_file(self, name, ref, path):
        return git_in(self.state, "--git-dir", os.path.join(self.state, "remotes", name), "show", f"{ref}:{path}")

    def test_opens_a_sync_pr_only_where_the_repo_is_behind(self):
        code, out, err = self.sync_repos()
        self.assertEqual(code, 1, err)
        branch = f"adlc/sync-{self.version}"
        self.assertIn("- o/behind: on 0.0.1; opened https://github.com/o/behind/pull/1", out)
        self.assertIn(f"- o/current: on {self.version}", out)
        self.assertIn("- o/copied: not synced yet", out)
        self.assertIn("- o/broken: failed: could not read .adlc/version: gh: Server Error (HTTP 500)", out)
        self.assertNotIn("o/other", out)
        self.assertNotIn("o/ADLC", out)
        [pr] = self.created()
        self.assertEqual((pr["repo"], pr["head"], pr["base"], pr["title"]),
                         ("o/behind", branch, "main", f"chore(adlc): sync to {self.version}"))
        self.assertIn(f"from ADLC 0.0.1 to {self.version}", pr["body"])
        self.assertIn("- update .adlc/version", pr["body"])
        self.assertIn("**Breaking**", pr["body"])
        self.assertIn(f"## ADLC {self.version}", pr["body"])
        self.assertIn("## ADLC 0.1.0", pr["body"])
        self.assertEqual(self.remote_file("o/behind", branch, ".adlc/version"), self.version)
        self.assertEqual(self.remote_file("o/behind", branch, "AGENTS.md"), "# mine")
        self.assertEqual(self.remote_file("o/behind", "main", ".adlc/version"), "0.0.1")
        with open(self.env["GITHUB_STEP_SUMMARY"]) as f:
            self.assertEqual(f.read(), out)

    def test_dry_run_and_an_open_pr_open_nothing(self):
        code, out, _ = self.sync_repos("--dry-run")
        self.assertIn(f"- o/behind: on 0.0.1; would open a PR to sync to {self.version}", out)
        with open(os.path.join(self.state, "open", "o_behind"), "w") as f:
            json.dump([{"url": "https://github.com/o/behind/pull/7"}], f)
        code, out, _ = self.sync_repos()
        self.assertIn("- o/behind: on 0.0.1; sync PR already open: https://github.com/o/behind/pull/7", out)
        self.assertEqual(self.created(), [])

    def test_needs_a_token_and_a_release_checkout(self):
        self.env["GH_TOKEN"] = ""
        code, _, err = self.sync_repos()
        self.assertNotEqual(code, 0)
        self.assertIn("GH_TOKEN", err)
        self.env["GH_TOKEN"] = "t"
        git_in(self.adlc, "commit", "-q", "--allow-empty", "-m", "unreleased")
        code, _, err = self.sync_repos()
        self.assertIn("release tag", err)
        self.assertEqual(self.created(), [])


class Manifest(unittest.TestCase):
    def test_workflow_manifest_is_current(self):
        code, _, err = run(["manifest", "--check"])
        self.assertEqual(code, 0, err)

    def test_check_fails_until_write(self):
        d = os.path.join(tempfile.mkdtemp(), "ADLC")
        for sub in ("scripts", "templates", ".claude-plugin", ".github"):
            shutil.copytree(os.path.join(ROOT, sub), os.path.join(d, sub))
        script = os.path.join(d, "scripts", "adlc.py")
        with open(os.path.join(d, "templates", "pull_request_template.md"), "a") as f:
            f.write("changed\n")
        check = [sys.executable, script, "manifest", "--check"]
        self.assertEqual(subprocess.run(check, capture_output=True).returncode, 1)
        subprocess.run([sys.executable, script, "manifest", "--write"], check=True)
        self.assertEqual(subprocess.run(check, capture_output=True).returncode, 0)

    def test_sources_exist_and_callers_pin_the_shared_workflow_of_their_name(self):
        adlc = load_adlc()
        for _, source in adlc.MANAGED + adlc.MANAGED_RELEASES + adlc.SEEDS + adlc.SEEDS_RELEASES:
            if source:
                self.assertTrue(os.path.isfile(os.path.join(ROOT, source)), source)
        callers = [s for p, s in adlc.MANAGED + adlc.MANAGED_RELEASES if p.startswith(".github/workflows/")]
        self.assertEqual(len(callers), 5)
        for source in callers:
            with open(os.path.join(ROOT, source)) as f:
                uses = re.findall(r"(?m)^\s+uses: (\S+)", f.read())
            name = os.path.basename(source)
            self.assertEqual(uses, [f"anandfrancis93/ADLC/.github/workflows/{name}@v{{{{ADLC_VERSION}}}}"], source)
            with open(os.path.join(ROOT, ".github", "workflows", name)) as f:
                self.assertIn("\non:\n  workflow_call:", f.read(), name)


class Workflows(unittest.TestCase):
    """A job skipped on a review run reports success under its check name, so the required
    checks job must never run on pull_request_review."""

    def jobs(self, name):
        with open(os.path.join(ROOT, ".github", "workflows", name)) as f:
            text = f.read()
        return set(re.findall(r"^  ([a-z0-9-]+):$", text.split("\njobs:\n", 1)[1], re.M))

    def job(self, name, job):
        with open(os.path.join(ROOT, ".github", "workflows", name)) as f:
            text = f.read()
        # A job ends at the next job, or at the comment above it.
        return re.search(rf"(?ms)^  {job}:\n.*?(?=^  #|^  [a-z0-9-]+:\n|\Z)", text.split("\njobs:\n", 1)[1]).group(0)

    def test_tier_job_is_the_same_in_both_workflows_and_never_needs_approval_to_pass(self):
        job = self.job("adlc.yml", "tier")
        self.assertEqual(job, self.job("adlc-review.yml", "tier"))
        # The tier and the approval are steps of one job, so a failed tier posts a failed status.
        self.assertIn("adlc.py tier --explain", job)
        self.assertIn("adlc.py t3-status", job)
        self.assertNotIn("t3-approved --owner", job)
        self.assertNotIn("needs:", job)
        self.assertNotIn("continue-on-error", job)
        # Without pipefail, a failed git diff gives an empty list, which is T1.
        self.assertIn("      - id: tier\n        shell: bash\n        working-directory: pr\n", job)
        steps = re.split(r"(?m)^      - ", job)
        # The status step runs for each tier: with an if, T1 and T2 PRs would get no status and stay blocked.
        report = next(step for step in steps if step.startswith("name: Report the owner's approval\n"))
        self.assertNotRegex(report, r"(?m)^        if:")
        last = steps[-1]
        self.assertTrue(last.startswith("name: Block the merge when this job fails\n"), last)
        self.assertIn("\n        if: failure() || cancelled()\n", last)

    def test_tier_job_runs_no_file_from_the_pr(self):
        """The job can write statuses, so it runs only the ADLC's own adlc.py, at the commit of this workflow."""
        job = self.job("adlc.yml", "tier")
        steps = re.split(r"(?m)^      - ", job)[1:]
        uses = [step for step in steps if step.startswith("uses: ")]
        self.assertEqual(len(uses), 2)
        for step in uses:
            self.assertTrue(step.startswith("uses: actions/checkout@"), step)
            self.assertIn("\n          persist-credentials: false\n", step)
        self.assertIn("\n          repository: ${{ job.workflow_repository }}\n          ref: ${{ job.workflow_sha }}\n"
                      "          path: adlc-release\n", uses[0])
        self.assertIn("\n          path: pr\n", uses[1])
        # Each run script, without the comments above the next step.
        runs = ["\n".join(line for line in step.split("run: |\n", 1)[1].splitlines() if not line.lstrip().startswith("#"))
                for step in steps if "run: |\n" in step]
        calls = re.findall(r"python3[^|\n]*", "\n".join(runs))
        self.assertEqual(len(calls), 2, calls)
        for call in calls:
            self.assertRegex(call, r"^python3 -I (\.\./)?adlc-release/scripts/adlc\.py ", call)
        for script in runs:
            self.assertNotIn(".adlc/", script)
        self.assertNotIn("working-directory: pr", job.replace("      - id: tier\n        shell: bash\n"
                                                             "        working-directory: pr\n", ""))

    def test_tier_job_names_the_repo_of_each_gh_command(self):
        """Both checkouts of tier use path:, so the workspace is not a git clone, and gh cannot find the repo from git.
        gh api needs no repo: each of its paths names it."""
        for name in ("adlc.yml", "adlc-review.yml"):
            for step in re.split(r"(?m)^      - ", self.job(name, "tier"))[1:]:
                if "run: |\n" not in step:
                    continue
                for line in step.split("run: |\n", 1)[1].splitlines():
                    for cmd in re.findall(r"\bgh (?!api\b)[a-z]+ [a-z-]+", line):
                        self.assertTrue("\n          GH_REPO: ${{ github.repository }}\n" in step or "--repo" in line,
                                        f"{name}: {cmd}")
        # The test sees the commands it must.
        self.assertIn("gh pr edit", self.job("adlc.yml", "tier"))

    def test_label_changes_rerun_the_review_caller(self):
        with open(os.path.join(ROOT, "templates", "github", "workflows", "adlc-review.yml")) as f:
            self.assertIn("  pull_request:\n    types: [labeled, unlabeled]\n", f.read())
        self.assertIn("synchronize", self.job("adlc.yml", "tier"))

    def test_review_runs_only_review_jobs(self):
        self.assertEqual(self.jobs("adlc-review.yml"), {"tier", "review-budget"})
        self.assertEqual(self.jobs("adlc.yml"), {"tier", "checks"})
        with open(os.path.join(ROOT, "templates", "github", "workflows", "adlc.yml")) as f:
            self.assertNotIn("pull_request_review", f.read())

    def test_one_job_runs_every_check_and_reports_each_failure(self):
        """GitHub bills each job as at least one minute, so the checks are steps of one job."""
        steps = re.split(r"(?m)^      - ", self.job("adlc.yml", "checks"))[1:]

        def field(step, key):
            m = re.search(rf"(?m)^(?:        )?{key}: (.*)$", step)
            return m.group(1) if m else ""

        names = [field(step, "name") for step in steps]
        self.assertTrue({"drift", "protected", "secrets", "design-md", "fast-check", "full-test"} <= set(names))
        self.assertEqual(names[1], "drift")
        for step in steps[2:]:
            self.assertIn("!cancelled()", field(step, "if"), step.splitlines()[0])
        # Only design-md may fail without failing the job; it was never a required check.
        self.assertEqual([n for n, step in zip(names, steps) if "continue-on-error" in step], ["design-md"])
        self.assertEqual(field(steps[names.index("fast-check")], "shell"), "bash")
        # The PR's code runs in this job, so its token can only read.
        self.assertIn("\n    permissions:\n      contents: read\n    steps:\n", self.job("adlc.yml", "checks"))

    def test_only_the_tier_jobs_write_statuses(self):
        tier_scopes = ("\n    permissions:\n      actions: read\n      checks: read\n      contents: read\n"
                       "      issues: write\n      pull-requests: write\n      statuses: write\n")
        for name in ("adlc.yml", "adlc-review.yml"):
            with open(os.path.join(ROOT, ".github", "workflows", name)) as f:
                head = f.read().split("\njobs:\n", 1)[0]
            # With no workflow-level block, a job without its own block gets all that the caller grants.
            self.assertNotRegex(head, r"(?m)^permissions:", name)
            self.assertIn(tier_scopes, self.job(name, "tier"), name)
            for other in self.jobs(name):
                job = self.job(name, other)
                self.assertRegex(job, r"(?m)^    permissions:\n      \w", f"{name}: {other}")
                self.assertNotIn("actions: write", job, f"{name}: {other}")
                if other != "tier":
                    self.assertNotIn("statuses: write", job, f"{name}: {other}")
        callers = os.path.join(ROOT, "templates", "github", "workflows")
        for name in ("adlc.yml", "adlc-review.yml"):
            with open(os.path.join(callers, name)) as f:
                head = f.read().split("\njobs:\n", 1)[0]
            self.assertIn("\n  actions: read\n", head, name)
            self.assertIn("\n  statuses: write\n", head, name)
            self.assertNotIn("actions: write", head, name)
        for path in (os.path.join(callers, "adlc-dependabot.yml"),
                     os.path.join(ROOT, ".github", "workflows", "adlc-dependabot.yml")):
            with open(path) as f:
                self.assertIn("\n  statuses: write\n", f.read().split("\njobs:\n", 1)[0], path)

    def test_one_status_name_everywhere(self):
        """Each repo requires adlc / t3-approval, the name the check had as a job in a caller job called adlc."""
        for name in ("adlc.yml", "adlc-review.yml", "adlc-dependabot.yml"):
            with open(os.path.join(ROOT, ".github", "workflows", name)) as f:
                text = f.read()
            self.assertIn("/statuses/$HEAD", text, name)
            self.assertEqual(set(re.findall(r'-f context="([^"]*)"', text)), {"adlc / t3-approval"}, name)
            self.assertEqual(text.count("/statuses/"), len(re.findall(r'-f context="', text)), name)
        for name in ("adlc.yml", "adlc-review.yml"):
            with open(os.path.join(ROOT, "templates", "github", "workflows", name)) as f:
                self.assertIn("\njobs:\n  adlc:\n", f.read(), name)


def step_script(workflow, name):
    """The run script of the step called name in this repo's workflow, without its indent."""
    with open(os.path.join(ROOT, ".github", "workflows", workflow)) as f:
        lines = f.read().split("\n")
    start = next(i for i, line in enumerate(lines) if line.strip() == f"- name: {name}")
    run_line = next(i for i in range(start, len(lines)) if lines[i].strip() == "run: |")
    indent = len(lines[run_line]) - len(lines[run_line].lstrip()) + 2
    script = []
    for line in lines[run_line + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) < indent:
            break
        script.append(line[indent:])
    return "\n".join(script)


# Answers fixed GitHub API requests from api.json: {"METHOD path": [answer, ...]}, the path without its query.
# Each request takes the next answer of its key, and the last answer repeats. An answer is {"body": ...},
# or {"status": 404} for an error. Each request goes to log.jsonl, with its -f fields.
# --jq runs jq -r, as gh prints strings raw.
FAKE_API_GH = r"""
import json, os, subprocess, sys
state = os.environ["FAKE_GH_STATE"]
args = sys.argv[1:]
if args[:1] != ["api"]:
    sys.exit("fake gh: unexpected " + " ".join(args))
method, jq, rest, fields, i = "GET", None, [], {}, 1
while i < len(args):
    if args[i] in ("-X", "--method"):
        method, i = args[i + 1], i + 2
    elif args[i] in ("-f", "-F", "--raw-field", "--field"):
        key, _, value = args[i + 1].partition("=")
        fields[key], i = value, i + 2
    elif args[i] in ("-q", "--jq"):
        jq, i = args[i + 1], i + 2
    elif args[i] == "--paginate":
        i += 1
    else:
        rest.append(args[i])
        i += 1
path = rest[0]
with open(os.path.join(state, "log.jsonl"), "a") as f:
    f.write(json.dumps({"method": method, "path": path, "fields": fields}) + "\n")
key = method + " " + path.split("?")[0]
with open(os.path.join(state, "api.json")) as f:
    answers = json.load(f).get(key)
if not answers:
    sys.exit("fake gh: no answer for " + key)
count = os.path.join(state, "count-" + key.replace("/", "_").replace(" ", "_"))
n = int(open(count).read()) if os.path.exists(count) else 0
with open(count, "w") as f:
    f.write(str(n + 1))
answer = answers[min(n, len(answers) - 1)]
if answer.get("status", 200) >= 400:
    sys.exit("gh: Error (HTTP %d)" % answer["status"])
out = json.dumps(answer.get("body"))
if jq:
    out = subprocess.run(["jq", "-r", jq], input=out, capture_output=True, text=True, check=True).stdout
print(out)
"""


class Seq(list):
    """The answers to one request, in order, as in api.json."""


class StepScript(unittest.TestCase):
    """Runs the script of one workflow step against a fake gh, as GitHub runs it."""

    def setUp(self):
        self.state = tempfile.mkdtemp()
        bin_dir = os.path.join(self.state, "bin")
        os.makedirs(bin_dir)
        with open(os.path.join(bin_dir, "gh"), "w") as f:
            f.write(f"#!{sys.executable}\n{FAKE_API_GH}")
        os.chmod(os.path.join(bin_dir, "gh"), 0o755)
        self.env = {"PATH": bin_dir + os.pathsep + os.environ["PATH"], "FAKE_GH_STATE": self.state,
                    "GH_TOKEN": "t", "GITHUB_REPOSITORY": "o/r", "GITHUB_RUN_ID": "9", "GITHUB_RUN_ATTEMPT": "1",
                    "PR": "5", "HEAD": "h2"}

    def serve(self, answers):
        """answers: {"METHOD path": body, or a Seq of answers as in api.json}."""
        api = {k: list(v) if isinstance(v, Seq) else [{"body": v}] for k, v in answers.items()}
        with open(os.path.join(self.state, "api.json"), "w") as f:
            json.dump(api, f)
        for name in os.listdir(self.state):
            if name.startswith("count-") or name == "log.jsonl":
                os.remove(os.path.join(self.state, name))

    def requests(self, method=None):
        path = os.path.join(self.state, "log.jsonl")
        if not os.path.exists(path):
            return []
        with open(path) as f:
            log = [json.loads(line) for line in f]
        return [e["path"] for e in log if method in (None, e["method"])]

    def posts(self):
        """The fields of each POST, in order."""
        with open(os.path.join(self.state, "log.jsonl")) as f:
            return [e["fields"] for e in map(json.loads, f) if e["method"] == "POST"]

    def run_step(self, command, workflow, step, cwd=None, **env):
        p = subprocess.run([*command, step_script(workflow, step)], capture_output=True, text=True, cwd=cwd,
                           env={**os.environ, **self.env, **env})
        return p.returncode, p.stdout + p.stderr


class DropStep(StepScript):
    STEP = "Drop the T3 approval label after a new commit"
    LABEL = "repos/o/r/issues/5/labels/adlc:t3-approved"

    def drop(self, events, attempt="1"):
        self.serve({"GET repos/o/r/actions/runs/9": {"id": 9, "created_at": "2026-10-23T19:51:26Z",
                                                     "run_started_at": "2026-10-23T20:00:00Z"},
                    "GET repos/o/r/issues/5/events": events,
                    "GET repos/o/r/commits/h2/check-suites": {"check_suites": [{"created_at": "2026-10-23T10:00:00Z"}]},
                    "DELETE " + self.LABEL: Seq([{"status": 404}])})
        code, out = self.run_step(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c"], "adlc.yml", self.STEP,
                                  GITHUB_RUN_ATTEMPT=attempt)
        self.assertEqual(code, 0, out)
        return self.requests("DELETE")

    def label(self, event, at, login="anand", name="adlc:t3-approved", id=1):
        return {"id": id, "event": event, "actor": {"login": login}, "label": {"name": name}, "created_at": at}

    def test_drop_step_keeps_a_label_added_after_the_push(self):
        after = self.label("labeled", "2026-10-23T19:59:36Z")
        for attempt in ("1", "2"):
            self.assertEqual(self.drop([after], attempt), [], attempt)
            self.assertEqual(self.drop([self.label("labeled", "2026-10-23T19:00:00Z", id=0), after], attempt), [])
        # Older than the run: an approval of the commit before the push. The check suites of a commit that
        # a force push brings back are older than the label, so they do not count here.
        self.assertEqual(self.drop([self.label("labeled", "2026-10-23T19:51:00Z")]), [self.LABEL])
        self.assertEqual(self.drop([self.label("labeled", "2026-10-23T19:51:26Z")]), [self.LABEL])
        self.assertEqual(self.drop([after, self.label("unlabeled", "2026-10-23T20:00:00Z", id=2)]), [self.LABEL])
        self.assertEqual(self.drop([self.label("labeled", "2026-10-23T20:00:00Z", name="adlc:T3")]), [self.LABEL])
        self.assertEqual(self.drop([]), [self.LABEL])


BASH = ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c"]
RUN_URL = "https://github.com/o/r/actions/runs/9"


class StatusStep(StepScript):
    STEP = "Report the owner's approval"
    LABEL = {"event": "labeled", "actor": {"login": "anand"}, "label": {"name": "adlc:t3-approved"},
             "created_at": "2026-10-24T06:10:00Z"}

    def report(self, tier="T3", events=Seq([{"body": []}]), reviews=()):
        """Runs the step in a workspace whose ADLC checkout holds this repo's script."""
        repo = os.path.join(self.state, "workspace")
        os.makedirs(os.path.join(repo, "adlc-release", "scripts"), exist_ok=True)
        shutil.copy(SCRIPT, os.path.join(repo, "adlc-release", "scripts", "adlc.py"))
        self.serve({"GET repos/o/r/pulls/5/reviews": list(reviews),
                    "GET repos/o/r/issues/5/events": events,
                    "GET repos/o/r/commits/h2/check-suites": {"check_suites": [{"created_at": "2026-10-24T06:00:00Z"}]},
                    "POST repos/o/r/statuses/h2": {}})
        return self.run_step(BASH, "adlc.yml", self.STEP, cwd=repo, TIER=tier, OWNER="anand", RUN_URL=RUN_URL,
                             RUNNER_TEMP=self.state)

    def states(self):
        posts = self.posts()
        for post in posts:
            self.assertEqual(post["context"], "adlc / t3-approval")
            self.assertEqual(post["target_url"], RUN_URL)
            self.assertLessEqual(len(post["description"]), 140)
        self.assertEqual({p for p in self.requests("POST")}, {"repos/o/r/statuses/h2"} if posts else set())
        return [p["state"] for p in posts]

    def test_waiting_t3_pr_posts_pending_and_passes(self):
        code, out = self.report()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.states(), ["pending"])

    def test_approved_t3_pr_posts_success(self):
        code, out = self.report(events=Seq([{"body": [self.LABEL]}]))
        self.assertEqual(code, 0, out)
        self.assertEqual(self.states(), ["success"])
        code, out = self.report(reviews=[{"user": {"login": "anand"}, "state": "APPROVED", "commit_id": "h2"}])
        self.assertEqual(code, 0, out)
        self.assertEqual(self.states(), ["success"])

    def test_t1_and_t2_post_success_without_reading_the_pr(self):
        for tier in ("T1", "T2"):
            code, out = self.report(tier)
            self.assertEqual(code, 0, out)
            self.assertEqual(self.states(), ["success"], tier)
            self.assertEqual(self.requests("GET"), [], tier)

    def test_status_follows_an_approval_during_the_step(self):
        code, out = self.report(events=Seq([{"body": []}, {"body": [self.LABEL]}]))
        self.assertEqual(code, 0, out)
        self.assertEqual(self.states(), ["pending", "success"])

    def test_status_step_fails_when_the_approval_keeps_changing(self):
        code, out = self.report(events=Seq([{"body": []}, {"body": [self.LABEL]}] * 3))
        self.assertEqual(code, 1, out)
        self.assertEqual(self.states(), ["pending", "success"] * 2 + ["pending"])
        self.assertIn("::error::", out)

    def test_failed_job_posts_a_failed_status(self):
        self.serve({"POST repos/o/r/statuses/h2": {}})
        code, out = self.run_step(BASH, "adlc.yml", "Block the merge when this job fails", RUN_URL=RUN_URL)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.states(), ["failure"])


class DependabotStep(StepScript):
    STEP = "Report that Dependabot PRs need no owner approval"

    def test_dependabot_prs_need_no_owner_approval(self):
        self.serve({"POST repos/o/r/statuses/h2": {}})
        code, out = self.run_step(BASH, "adlc-dependabot.yml", self.STEP, RUN_URL=RUN_URL)
        self.assertEqual(code, 0, out)
        self.assertEqual([(p["context"], p["state"]) for p in self.posts()], [("adlc / t3-approval", "success")])
        self.assertEqual(self.requests("POST"), ["repos/o/r/statuses/h2"])
        # The status comes first, so a Dependabot PR that the tier step cannot tier still passes, as before.
        with open(os.path.join(ROOT, ".github", "workflows", "adlc-dependabot.yml")) as f:
            text = f.read()
        self.assertLess(text.index(f"- name: {self.STEP}"), text.index("- id: meta"))
