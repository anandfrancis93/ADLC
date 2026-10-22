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
                uses = re.findall(r"uses: (\S+)", f.read())
            name = os.path.basename(source)
            self.assertEqual(uses, [f"anandfrancis93/ADLC/.github/workflows/{name}@v{{{{ADLC_VERSION}}}}"], source)
            with open(os.path.join(ROOT, ".github", "workflows", name)) as f:
                self.assertIn("\non:\n  workflow_call:", f.read(), name)


class Workflows(unittest.TestCase):
    """A job skipped on a review run reports success under its check name, so required checks
    other than t3-approval must never run on pull_request_review."""

    def jobs(self, name):
        with open(os.path.join(ROOT, ".github", "workflows", name)) as f:
            text = f.read()
        return set(re.findall(r"^  ([a-z0-9-]+):$", text.split("\njobs:\n", 1)[1], re.M))

    def test_review_runs_only_review_jobs(self):
        self.assertEqual(self.jobs("adlc-review.yml"), {"tier", "t3-approval", "review-budget"})
        self.assertTrue({"drift", "fast-check", "secrets", "protected", "full-test"} <= self.jobs("adlc.yml"))
        with open(os.path.join(ROOT, "templates", "github", "workflows", "adlc.yml")) as f:
            self.assertNotIn("pull_request_review", f.read())
