"""Tests for the implement-tickets workflow with tickets in .scratch/ markdown files (tracker "files").

The workflow is a Claude Code Workflow script. These tests run it under Node with a stub
agent() that returns canned results per agent label, and assert on the agents it starts and
what it returns. No model, git or GitHub call is made.
"""

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
ROOT = SKILL_DIR.parents[3]
SCRIPT = SKILL_DIR / "workflows" / "implement-tickets.js"
NODE = shutil.which("node")

# The stub runtime. SCENARIO is a JSON object:
#   args       the workflow's args
#   plan       the Plan agent's result
#   overrides  {label: result}; a label mapped to null makes that agent fail
HARNESS = r"""
const SCENARIO = JSON.parse(process.env.SCENARIO);
const calls = [];
let active = 0, peak = 0;
const args = SCENARIO.args;
const log = () => {};
const phase = () => {};
const ticketOf = label => Number((label.match(/^\S+ (\d+)/) || [])[1]);

function canned(label, prompt) {
  if (label in SCENARIO.overrides) return SCENARIO.overrides[label];
  const n = ticketOf(label);
  if (label === 'plan') return SCENARIO.plan;
  if (label.startsWith('build')) {
    const base = prompt.match(/from \`origin\/([^`]+)\`/)[1];
    return { status: 'done', branch: 'feat/' + Number(n), base, headSha: 'b' + n,
             criteria: [{ criterion: 'c', met: true }], checks: [], decisions: [], deviations: [] };
  }
  if (label.startsWith('pr')) {
    const base = prompt.match(/its base is \`([^`]+)\`/)[1];
    return { number: 100 + Number(n), url: 'https://example.test/pr/' + n, headSha: 'b' + n, base,
             decisions: [], deviations: [] };
  }
  if (label.startsWith('review')) {
    return { reviewedSha: 'b' + n, skillsUsed: [], findings: [], limits: [], decisions: [], deviations: [] };
  }
  if (label.startsWith('fix')) {
    return { headSha: 'f' + n, pushed: true, fixed: [], refuted: [], needsDecision: [], checks: [],
             decisions: [], deviations: [] };
  }
  if (label.startsWith('wait')) {
    return { headSha: 'b' + n, routineReviewLanded: true, ci: 'passed', failingChecks: [], deviations: [] };
  }
  if (label.startsWith('audit')) {
    return { headSha: 'b' + n, unresolved: [], needsDecision: [], ci: 'passed',
             counts: { total: 0, unresolved: 0, addressed: 0, refuted: 0, needsDecision: 0 }, deviations: [] };
  }
  if (label === 'sync chain') return { merges: [], decisions: [], deviations: [] };
  if (label === 'run report') return { status: 'ok', report: 'report' };
  throw new Error('no canned result for ' + label);
}

async function agent(prompt, opts) {
  active++;
  peak = Math.max(peak, active);
  calls.push({ label: opts.label, model: opts.model || null, isolation: opts.isolation || null, prompt });
  await new Promise(r => setTimeout(r, 2));
  active--;
  return canned(opts.label, prompt);
}

(async () => {
  let out = null, error = null;
  try {
    out = await (async () => {
/*SCRIPT*/
    })();
  } catch (e) {
    error = e.message;
  }
  process.stdout.write(JSON.stringify({ out, error, peak, calls }));
})();
"""


def tid(n):
    return f"{n:02d}"


def ticket(number, blocked_by=(), status="ready-for-agent", state="open", open_pr=None):
    path = f".scratch/feat/issues/{tid(number)}-t{number}.md"
    return {
        "id": tid(number), "title": f"ticket {number}", "path": path, "status": status, "state": state,
        "blockedBy": [tid(b) for b in blocked_by], "openPr": open_pr,
        "text": f"# {tid(number)}: ticket {number}\n\n**Status:** {status}\n\n- [ ] criterion {number}\n",
    }


def plan(tickets, blocker_states=(), review_routine=True):
    return {
        "repo": "o/r", "defaultBranch": "main", "featureDir": ".scratch/feat",
        "featureDirAbs": "/work/r/.scratch/feat",
        "spec": {"path": ".scratch/feat/spec.md", "title": "spec", "text": "# spec\n\nThe spec body.\n"},
        "reviewRoutine": review_routine,
        "tickets": tickets, "blockerStates": list(blocker_states),
        "checks": ["make test"], "decisions": [], "deviations": [],
    }


def run(ticket_list, blocker_states=(), overrides=None, review_routine=True, plan_extra=None, **extra_args):
    body = SCRIPT.read_text().replace("export const meta", "const meta", 1)
    source = HARNESS.replace("/*SCRIPT*/", body)
    scenario = {
        "args": {"feature": "feat", **extra_args},
        "plan": {**plan(ticket_list, blocker_states, review_routine), **(plan_extra or {})},
        "overrides": overrides or {},
    }
    result = subprocess.run(
        [NODE, "-"], input=source, capture_output=True, text=True, timeout=60,
        env={**os.environ, "SCENARIO": json.dumps(scenario)},
    )
    if result.returncode != 0:
        raise AssertionError(f"node failed:\n{result.stderr}")
    return json.loads(result.stdout)


def labels(result, prefix):
    return [c["label"] for c in result["calls"] if c["label"].startswith(prefix)]


def prompt(result, label):
    return next(c["prompt"] for c in result["calls"] if c["label"] == label)


def by_ticket(result):
    return {int(t["ticket"]): t for t in result["out"]["tickets"]}


@unittest.skipUnless(NODE or os.environ.get("CI"), "node is not installed")
class FilesWorkflowTest(unittest.TestCase):
    def setUp(self):
        if not NODE:
            self.fail("node is required in CI to test the implement-tickets workflow")

    def test_every_agent_reads_the_chain_rule(self):
        r = run([ticket(2), ticket(3, [2])])
        for c in r["calls"]:
            self.assertIn("Never run `gh stack`", c["prompt"], c["label"])

    def test_each_pr_gets_its_place_in_the_chain_from_the_bottom(self):
        r = run([ticket(2), ticket(3, [2]), ticket(4, [3])])
        for n, place in ((2, 1), (3, 2), (4, 3)):
            text = " ".join(prompt(r, f"pr {n:02d}").split())
            self.assertIn(f"PR {place} of the chain, counting from the bottom", text)
        self.assertEqual({2: 1, 3: 2, 4: 3}, {n: t["place"]["height"] for n, t in by_ticket(r).items()})

    def test_the_pr_prompt_and_the_report_state_the_same_place_rule(self):
        r = run([ticket(2), ticket(3, [2])])
        rule = "PR 1 is the one whose base is `main`, and each other PR is one more than the highest PR it depends on"
        self.assertIn(rule, " ".join(prompt(r, "pr 03").split()))
        self.assertIn(rule, " ".join(prompt(r, "run report").split()))

    def test_a_pr_with_two_blockers_is_above_the_higher_one(self):
        for blockers in ([2, 3], [3, 2]):
            r = run([ticket(2), ticket(3, [2]), ticket(4, blockers)])
            self.assertEqual(3, by_ticket(r)[4]["place"]["height"], blockers)

    def test_places_above_a_blocker_outside_the_run_count_from_it(self):
        outside = [{"id": "09", "state": "open", "openPrBranch": "feat/9"}]
        r = run([ticket(5, [9]), ticket(6, [5])], blocker_states=outside)
        self.assertIn("PR 1 above the PR for `feat/9`, which is outside this run",
                      " ".join(prompt(r, "pr 05").split()))
        self.assertIn("PR 2 above the PR for `feat/9`, which is outside this run",
                      " ".join(prompt(r, "pr 06").split()))
        self.assertEqual({"height": 2, "anchor": "feat/9"}, by_ticket(r)[6]["place"])

    def test_the_place_follows_the_base_the_build_returns(self):
        build3 = {"status": "done", "branch": "feat/3", "base": "main", "headSha": "b3",
                  "criteria": [{"criterion": "c", "met": True}], "checks": [], "decisions": [], "deviations": []}
        r = run([ticket(2), ticket(3, [2])], overrides={"build 03": build3})
        self.assertIn("PR 1 of the chain", " ".join(prompt(r, "pr 03").split()))
        texts = [e["text"] for e in r["out"]["ledger"] if e["kind"] == "deviation"]
        self.assertTrue(any("not the planned `feat/2`" in t for t in texts), texts)

    def test_wait_and_report_agents_get_only_the_chain_rule(self):
        r = run([ticket(2)])
        for c in r["calls"]:
            if c["label"].startswith("wait") or c["label"] == "run report":
                self.assertNotIn("Rules for every step of this run", c["prompt"], c["label"])

    def test_bases_each_ticket_on_its_blocker(self):
        r = run([ticket(2), ticket(3, [2]), ticket(4, [3])])
        self.assertIsNone(r["error"])
        bases = {n: t["base"] for n, t in by_ticket(r).items()}
        self.assertEqual(bases, {2: "main", 3: "feat/2", 4: "feat/3"})
        order = labels(r, "build")
        self.assertEqual(order, ["build 02", "build 03", "build 04"])
        # A blocked ticket starts once its blocker's PR is open, not after its review.
        self.assertLess(r["calls"].index(next(c for c in r["calls"] if c["label"] == "pr 02")),
                        r["calls"].index(next(c for c in r["calls"] if c["label"] == "build 03")))
        self.assertIn("sync chain", labels(r, "sync"))

    def test_runs_at_most_four_agents_at_once(self):
        r = run([ticket(n) for n in range(2, 12)])
        self.assertIsNone(r["error"])
        self.assertEqual(r["peak"], 4)
        self.assertEqual(len(labels(r, "build")), 10)

    def test_uses_the_agreed_model_for_each_step(self):
        r = run([ticket(2)])
        models = {c["label"].split(" ")[0]: c["model"] for c in r["calls"]}
        self.assertEqual(models, {
            "plan": "sonnet", "build": "opus", "pr": "sonnet", "review": "opus",
            "wait": "haiku", "audit": "opus", "run": "sonnet",
        })
        isolated = {c["label"] for c in r["calls"] if c["isolation"] == "worktree"}
        self.assertEqual(isolated, {"build 02"})

    def test_refuses_a_dependency_cycle_before_building(self):
        r = run([ticket(2, [3]), ticket(3, [2])])
        self.assertIn("cycle", r["error"])
        self.assertEqual(labels(r, "build"), [])

    def test_skips_tickets_that_are_closed_or_not_ready(self):
        r = run([ticket(2), ticket(3, status="needs-triage"), ticket(4, state="closed")])
        self.assertEqual(labels(r, "build"), ["build 02"])
        self.assertEqual(r["out"]["skipped"], ["03", "04"])
        texts = [e["text"] for e in r["out"]["ledger"]]
        self.assertTrue(any("ticket 03" in t and "ready-for-agent" in t for t in texts))

    def test_explicit_ticket_list_builds_unlabelled_tickets(self):
        r = run([ticket(2, status="")], tickets=[2])
        self.assertEqual(labels(r, "build"), ["build 02"])

    def test_two_blockers_branch_from_one_and_merge_the_other(self):
        r = run([ticket(2), ticket(3), ticket(4, [2, 3])])
        p = prompt(r, "build 04")
        self.assertIn("git fetch origin feat/2 feat/3", p)
        self.assertIn("merge `origin/feat/3`", p)
        self.assertEqual(by_ticket(r)[4]["base"], "feat/2")

    def test_bases_on_an_open_blocker_outside_the_run(self):
        r = run([ticket(2, [9])], [{"id": "09", "state": "open", "openPrBranch": "feat/9"}])
        self.assertEqual(by_ticket(r)[2]["base"], "feat/9")

    def test_does_not_build_on_an_open_outside_blocker_without_a_pr(self):
        r = run([ticket(2, [9])], [{"id": "09", "state": "open"}])
        self.assertEqual(labels(r, "build"), [])
        self.assertEqual(by_ticket(r)[2]["status"], "not built")

    def test_does_not_build_when_an_outside_blocker_has_no_state(self):
        r = run([ticket(2, [9])])
        self.assertEqual(labels(r, "build"), [])
        self.assertEqual(by_ticket(r)[2]["status"], "not built")
        texts = [e["text"] for e in r["out"]["ledger"]]
        self.assertTrue(any("no state for blocker 09" in t for t in texts))

    def test_does_not_build_after_a_blocker_fails(self):
        r = run([ticket(2), ticket(3, [2])], overrides={"build 02": None})
        self.assertEqual(labels(r, "build"), ["build 02"])
        self.assertEqual(by_ticket(r)[3]["status"], "not built")

    def test_plan_only_stops_before_building(self):
        r = run([ticket(2)], planOnly=True)
        self.assertEqual([c["label"] for c in r["calls"]], ["plan"])
        self.assertEqual(r["out"]["inScope"], ["02"])

    def test_reports_not_audited_when_the_audit_fails(self):
        r = run([ticket(2)], overrides={"audit 02 r1": None})
        self.assertEqual(by_ticket(r)[2]["status"], "not audited")

    def test_fixes_review_findings_and_audits_them(self):
        finding = {"id": "F1", "severity": "major", "location": "a.go:1", "claim": "c",
                   "evidence": "e", "source": "review"}
        r = run([ticket(2)], overrides={
            "review 02": {"reviewedSha": "b2", "skillsUsed": [], "findings": [finding], "limits": [],
                          "decisions": [], "deviations": []},
        })
        self.assertIn('"F1"', prompt(r, "fix 02 r1"))
        self.assertIn('"F1"', prompt(r, "audit 02 r1"))
        self.assertIn("head f2", prompt(r, "wait 02 r1.1"))
        self.assertEqual(by_ticket(r)[2]["status"], "clean")

    def test_an_unpushed_fix_does_not_move_the_head(self):
        finding = {"id": "F1", "severity": "minor", "location": "a.go:1", "claim": "c",
                   "evidence": "e", "source": "review"}
        r = run([ticket(2)], overrides={
            "review 02": {"reviewedSha": "b2", "skillsUsed": [], "findings": [finding], "limits": [],
                          "decisions": [], "deviations": []},
            "fix 02 r1": {"headSha": "local", "pushed": False, "fixed": [], "refuted": [],
                          "needsDecision": [], "checks": [], "decisions": [], "deviations": []},
        })
        self.assertIn("head b2", prompt(r, "wait 02 r1.1"))

    def test_stops_after_the_last_fix_round_with_findings_open(self):
        open_finding = {"id": "A1", "severity": "major", "location": "a.go:1", "claim": "c",
                        "evidence": "e", "source": "audit"}
        audit = {"headSha": "b2", "unresolved": [open_finding], "needsDecision": [],
                 "counts": {"total": 1, "unresolved": 1, "addressed": 0, "refuted": 0, "needsDecision": 0},
                 "deviations": []}
        r = run([ticket(2)], overrides={"audit 02 r1": audit, "audit 02 r2": audit}, maxFixRounds=2)
        self.assertEqual(labels(r, "fix"), ["fix 02 r2"])
        t = by_ticket(r)[2]
        self.assertEqual(t["status"], "open findings")
        self.assertEqual([f["id"] for f in t["openFindings"]], ["A1"])

    def test_records_audit_counts_that_do_not_add_up(self):
        audit = {"headSha": "b2", "unresolved": [], "needsDecision": [],
                 "counts": {"total": 3, "unresolved": 0, "addressed": 1, "refuted": 0, "needsDecision": 0},
                 "deviations": []}
        r = run([ticket(2)], overrides={"audit 02 r1": audit})
        texts = [e["text"] for e in r["out"]["ledger"]]
        self.assertTrue(any("do not reconcile" in t for t in texts))

    def test_waits_again_until_the_routine_review_lands(self):
        pending = {"headSha": "b2", "routineReviewLanded": False, "ci": "pending", "failingChecks": [],
                   "deviations": []}
        r = run([ticket(2)], overrides={"wait 02 r1.1": pending})
        self.assertEqual(labels(r, "wait"), ["wait 02 r1.1", "wait 02 r1.2"])

    def test_without_the_routine_waits_for_ci_only_and_requests_no_review(self):
        r = run([ticket(2)], routine=False)
        self.assertIsNone(r["error"])
        # Polling stays with haiku: one CI-only wait, no routine review request anywhere.
        self.assertEqual(labels(r, "wait"), ["wait 02 r1.1"])
        wait = next(c for c in r["calls"] if c["label"] == "wait 02 r1.1")
        self.assertEqual(wait["model"], "haiku")
        self.assertIn("Check CI on pull request #", wait["prompt"])
        for c in r["calls"]:
            self.assertNotIn("cipherstash-agent", c["prompt"], c["label"])
        self.assertEqual(labels(r, "audit"), ["audit 02 r1"])
        # The audit neither polls CI nor waits for it.
        self.assertNotIn("wait up to 15 minutes", prompt(r, "audit 02 r1").lower())
        self.assertEqual(by_ticket(r)[2]["status"], "clean")

    def test_without_the_routine_waits_again_while_ci_is_pending(self):
        pending = {"headSha": "b2", "routineReviewLanded": False, "ci": "pending", "failingChecks": [],
                   "deviations": []}
        r = run([ticket(2)], routine=False, overrides={"wait 02 r1.1": pending})
        self.assertEqual(labels(r, "wait"), ["wait 02 r1.1", "wait 02 r1.2"])

    def test_without_the_routine_finished_ci_ends_the_wait(self):
        done = {"headSha": "b2", "routineReviewLanded": False, "ci": "passed", "failingChecks": [],
                "deviations": []}
        r = run([ticket(2)], routine=False, overrides={"wait 02 r1.1": done})
        self.assertEqual(labels(r, "wait"), ["wait 02 r1.1"])

    def test_audit_checks_ci_once_when_no_wait_reported(self):
        r = run([ticket(2)], routine=False, waitRounds=0)
        self.assertIn("Check CI's state on the PR's current head once",
                      " ".join(prompt(r, "audit 02 r1").split()))

    def test_plan_looks_for_the_routine_workflow(self):
        r = run([ticket(2)])
        self.assertIn(".github/workflows/claude-review.yml", prompt(r, "plan"))

    def test_routine_defaults_to_whether_the_repository_has_it(self):
        # This repository has the routine, so its Plan agent reports it and the run waits for it.
        self.assertTrue((ROOT / ".github" / "workflows" / "claude-review.yml").is_file())
        with_routine = run([ticket(2)], review_routine=True)
        self.assertEqual(labels(with_routine, "wait"), ["wait 02 r1.1"])
        self.assertIn("cipherstash-agent", prompt(with_routine, "pr 02"))
        without = run([ticket(2)], review_routine=False)
        self.assertNotIn("cipherstash-agent", prompt(without, "pr 02"))
        self.assertNotIn("cipherstash-agent", prompt(without, "wait 02 r1.1"))

    def test_routine_arg_overrides_what_the_plan_found(self):
        r = run([ticket(2)], review_routine=False, routine=True)
        self.assertEqual(labels(r, "wait"), ["wait 02 r1.1"])
        r = run([ticket(2)], review_routine=True, routine=False)
        self.assertNotIn("cipherstash-agent", prompt(r, "wait 02 r1.1"))

    def test_routine_is_off_when_the_plan_does_not_say(self):
        r = run([ticket(2)], review_routine=None)
        self.assertNotIn("cipherstash-agent", prompt(r, "wait 02 r1.1"))

    def test_routine_off_note_does_not_invent_what_the_plan_found(self):
        r = run([ticket(2)], review_routine=None)
        texts = [e["text"] for e in r["out"]["ledger"]]
        self.assertFalse(any("found no" in t for t in texts), texts)
        self.assertIn("deviation", [e["kind"] for e in r["out"]["ledger"]
                                    if "did not report" in e["text"]])

    def test_failing_ci_the_audit_did_not_list_is_an_open_finding(self):
        audit = {"headSha": "b2", "unresolved": [], "needsDecision": [], "ci": "failed",
                 "counts": {"total": 0, "unresolved": 0, "addressed": 0, "refuted": 0, "needsDecision": 0},
                 "deviations": []}
        r = run([ticket(2)], routine=False, maxFixRounds=1, overrides={"audit 02 r1": audit})
        t = by_ticket(r)[2]
        self.assertNotEqual(t["status"], "clean")
        self.assertEqual([f["id"] for f in t["openFindings"]], ["CI"])

    def test_failing_ci_gets_a_fix_round_when_the_audit_omits_it(self):
        failed = {"headSha": "b2", "unresolved": [], "needsDecision": [], "ci": "failed",
                  "counts": {"total": 0, "unresolved": 0, "addressed": 0, "refuted": 0, "needsDecision": 0},
                  "deviations": []}
        r = run([ticket(2)], routine=False, overrides={"audit 02 r1": failed})
        self.assertEqual(labels(r, "fix"), ["fix 02 r2"])
        self.assertIn('"source": "CI"', prompt(r, "fix 02 r2"))
        self.assertEqual(by_ticket(r)[2]["status"], "clean")

    def test_ci_that_has_not_passed_is_not_clean(self):
        no_findings = {"headSha": "b2", "unresolved": [], "needsDecision": [],
                       "counts": {"total": 0, "unresolved": 0, "addressed": 0, "refuted": 0, "needsDecision": 0},
                       "deviations": []}
        for routine in (True, False):
            r = run([ticket(2)], routine=routine, overrides={"audit 02 r1": {**no_findings, "ci": "pending"}})
            t = by_ticket(r)[2]
            self.assertEqual(t["status"], "ci pending", routine)
            self.assertEqual(t["ci"], "pending", routine)
        # An audit that leaves CI out, with no wait to fall back on, leaves CI unknown.
        r = run([ticket(2)], routine=False, waitRounds=0, overrides={"audit 02 r1": no_findings})
        self.assertEqual(by_ticket(r)[2]["status"], "ci unknown")
        for ci in ("passed", "none"):
            r = run([ticket(2)], routine=False, overrides={"audit 02 r1": {**no_findings, "ci": ci}})
            self.assertEqual(by_ticket(r)[2]["status"], "clean", ci)

    def test_audit_reports_ci_with_or_without_the_routine(self):
        for routine in (True, False):
            r = run([ticket(2)], routine=routine)
            self.assertIn('Report CI\'s state on the head as "ci"',
                          " ".join(prompt(r, "audit 02 r1").split()), routine)

    def test_audit_without_a_ci_state_is_a_deviation(self):
        audit = {"headSha": "b2", "unresolved": [], "needsDecision": [],
                 "counts": {"total": 0, "unresolved": 0, "addressed": 0, "refuted": 0, "needsDecision": 0},
                 "deviations": []}
        r = run([ticket(2)], routine=False, overrides={"audit 02 r1": audit})
        texts = [e["text"] for e in r["out"]["ledger"] if e["kind"] == "deviation"]
        self.assertTrue(any("did not report CI" in t for t in texts), texts)

    def test_build_and_review_name_a_fallback_without_mattpocock_skills(self):
        r = run([ticket(2)])
        build = " ".join(prompt(r, "build 02").split())
        self.assertIn("If `mattpocock-skills:tdd` cannot be loaded", build)
        self.assertIn("red, green, refactor", build[build.index("cannot be loaded"):])
        review = " ".join(prompt(r, "review 02").split())
        self.assertIn("If `mattpocock-skills:code-review` cannot be loaded", review)
        self.assertIn("review the diff against the ticket yourself", review)
        for text in (build, review):
            self.assertIn("record a deviation", text[text.index("cannot be loaded"):])

    def test_run_report_gets_every_ledger_entry(self):
        r = run([ticket(2), ticket(3, status="")])
        self.assertIn("Skipped ticket 03", prompt(r, "run report"))
        self.assertEqual(labels(r, "run"), ["run report"])


class ScratchTicketsTest(unittest.TestCase):
    """What differs from implement-tickets: tickets are files, not tracker issues."""

    def setUp(self):
        if not NODE:
            self.skipTest("node is not installed")

    def test_needs_a_feature(self):
        body = SCRIPT.read_text().replace("export const meta", "const meta", 1)
        scenario = {"args": {"tracker": "files", "tickets": [2]}, "plan": plan([ticket(2)]), "overrides": {}}
        result = subprocess.run(
            [NODE, "-"], input=HARNESS.replace("/*SCRIPT*/", body), capture_output=True, text=True,
            timeout=60, env={**os.environ, "SCENARIO": json.dumps(scenario)},
        )
        out = json.loads(result.stdout)
        self.assertIn("args.feature", out["error"])
        self.assertEqual(out["calls"], [])

    def test_a_feature_picks_the_files_tracker(self):
        r = run([ticket(2)])
        self.assertEqual(r["out"]["tracker"], "files")
        self.assertIn("Read every ticket file under `issues/`", prompt(r, "plan"))
        self.assertNotIn("GitHub's native issue dependencies", prompt(r, "plan"))

    def test_a_slug_names_a_directory_under_scratch_and_a_path_is_used_as_given(self):
        self.assertIn("`.scratch/feat`", prompt(run([ticket(2)], planOnly=True), "plan"))
        r = run([ticket(2)], planOnly=True, feature="docs/tickets/feat")
        self.assertIn("`docs/tickets/feat`", prompt(r, "plan"))

    def test_every_agent_that_judges_the_work_gets_the_ticket_text(self):
        finding = {"id": "F1", "severity": "major", "location": "a.go:1", "claim": "c",
                   "evidence": "e", "source": "review"}
        r = run([ticket(2)], overrides={
            "review 02": {"reviewedSha": "b2", "skillsUsed": [], "findings": [finding], "limits": [],
                          "decisions": [], "deviations": []},
        })
        for label in ("build 02", "pr 02", "review 02", "fix 02 r1", "audit 02 r1"):
            self.assertIn("- [ ] criterion 2", prompt(r, label), label)
            self.assertIn("/work/r/.scratch/feat/issues/02-t2.md", prompt(r, label), label)
        for label in ("build 02", "review 02"):
            self.assertIn("The spec body.", prompt(r, label), label)

    def test_no_agent_may_write_the_ticket_files(self):
        r = run([ticket(2), ticket(3, [2])])
        for c in r["calls"]:
            text = " ".join(c["prompt"].split())
            self.assertIn("Never add, change, move or delete anything under it", text, c["label"])
        self.assertIn("nothing under `.scratch/feat` is staged", " ".join(prompt(r, "build 02").split()))

    def test_the_pr_names_its_ticket_file_and_closes_no_issue(self):
        r = run([ticket(2)])
        text = prompt(r, "pr 02")
        self.assertIn("`Ticket: .scratch/feat/issues/02-t2.md`", text)
        self.assertNotIn("Closes #", text)

    def test_the_branch_is_named_after_the_ticket_file(self):
        self.assertIn("`feat/02-t2`", prompt(run([ticket(2)]), "build 02"))

    def test_ticket_ids_match_however_they_are_written(self):
        t3 = ticket(3, [2])
        t3["id"], t3["blockedBy"] = "3", ["2"]
        r = run([ticket(2), t3], tickets=["2", 3])
        self.assertEqual(labels(r, "build"), ["build 02", "build 03"])
        self.assertEqual(by_ticket(r)[3]["base"], "feat/2")

    def test_an_explicit_list_builds_only_the_tickets_it_names(self):
        r = run([ticket(2), ticket(3), ticket(4)], tickets=[3])
        self.assertEqual(labels(r, "build"), ["build 03"])

    def test_a_ticket_asked_for_without_a_file_is_a_deviation(self):
        r = run([ticket(2)], tickets=[2, 7])
        texts = [e["text"] for e in r["out"]["ledger"] if e["kind"] == "deviation"]
        self.assertTrue(any("Ticket 07 was asked for" in t for t in texts), texts)

    def test_a_skipped_ticket_reports_its_status(self):
        r = run([ticket(2), ticket(3, status="needs-info")])
        texts = [e["text"] for e in r["out"]["ledger"]]
        self.assertTrue(any('ticket 03' in t and '"needs-info"' in t for t in texts), texts)

    def test_the_report_names_each_ticket_file(self):
        r = run([ticket(2)])
        self.assertIn(".scratch/feat/issues/02-t2.md", prompt(r, "run report"))
        self.assertEqual(r["out"]["featureDir"], ".scratch/feat")

    def test_a_skipped_ticket_file_is_a_blocker_without_repeating_it_in_blocker_states(self):
        r = run([ticket(2, status="done", state="open"), ticket(3, [2])])
        self.assertEqual(labels(r, "build"), ["build 03"])
        self.assertEqual(by_ticket(r)[3]["base"], "main")
        r = run([ticket(2, status="needs-info"), ticket(3, [2])])
        self.assertEqual(by_ticket(r)[3]["status"], "not built")
        open_pr = {"number": 7, "url": "u", "branch": "feat/2-old", "merged": False}
        r = run([ticket(2, status="needs-info", open_pr=open_pr), ticket(3, [2])])
        self.assertEqual(by_ticket(r)[3]["base"], "feat/2-old")

    def test_a_closed_status_closes_the_ticket_even_when_listed(self):
        r = run([ticket(2, status="Resolved", state="open"), ticket(3)], tickets=[2, 3])
        self.assertEqual(labels(r, "build"), ["build 03"])

    def test_an_open_pr_is_continued_and_a_merged_one_is_not(self):
        open_pr = {"number": 7, "url": "u", "branch": "feat/2-old", "merged": False}
        r = run([ticket(2, open_pr=open_pr)])
        self.assertIn("check out the existing PR branch `feat/2-old`", prompt(r, "build 02"))
        self.assertIn("PR #7 is already open for it", prompt(r, "pr 02"))
        r = run([ticket(2, open_pr={**open_pr, "merged": True})])
        self.assertNotIn("feat/2-old", prompt(r, "build 02"))
        self.assertNotIn("PR #7", prompt(r, "pr 02"))

    def test_the_chain_syncs_bottom_up(self):
        r = run([ticket(4, [3]), ticket(3, [2]), ticket(2)])
        text = prompt(r, "sync chain")
        edges = json.loads(text[text.index("["):text.index("]") + 1])
        self.assertEqual([e["ticket"] for e in edges], ["02", "03", "04"])

    def test_blocker_state_ids_are_normalised(self):
        r = run([ticket(2, [9])], [{"id": "9", "state": "open", "openPrBranch": "feat/9"}])
        self.assertEqual(by_ticket(r)[2]["base"], "feat/9")

    def test_a_closed_blocker_outside_the_run_builds_on_the_base(self):
        r = run([ticket(3, [2])], [{"id": "02", "state": "closed"}])
        self.assertEqual(by_ticket(r)[3]["base"], "main")
        self.assertEqual(by_ticket(r)[3]["status"], "clean")

    def test_no_spec_and_no_absolute_directory(self):
        r = run([ticket(2)], plan_extra={"spec": None, "featureDirAbs": None})
        for label in ("build 02", "review 02"):
            self.assertIn("has no spec.md", prompt(r, label), label)
        for c in r["calls"]:
            self.assertNotIn("undefined", c["prompt"], c["label"])
            self.assertNotIn("also readable at", c["prompt"], c["label"])
        self.assertIsNone(r["out"]["spec"])

    def test_a_blocked_build_stops_its_dependents(self):
        blocked = {"status": "blocked", "blocker": "no db", "branch": "feat/2", "base": "main",
                   "criteria": [], "checks": [], "decisions": [], "deviations": []}
        r = run([ticket(2), ticket(3, [2])], overrides={"build 02": blocked})
        self.assertEqual({2: "not built", 3: "not built"}, {n: t["status"] for n, t in by_ticket(r).items()})
        self.assertTrue(any("Blocked: no db" in e["text"] for e in r["out"]["ledger"]))

    def test_tid_trims_and_drops_extra_zeros_and_a_trailing_slash(self):
        t3 = ticket(3)
        t3["id"] = " 003 "
        r = run([t3], tickets=["3"], feature="feat/")
        self.assertEqual(labels(r, "build"), ["build 03"])
        self.assertIn("`.scratch/feat`", prompt(r, "plan"))

    def test_tickets_left_out_of_an_explicit_list_get_a_reason(self):
        r = run([ticket(2), ticket(3)], tickets=[2])
        texts = [e["text"] for e in r["out"]["ledger"]]
        self.assertIn("Skipped ticket 03 because args.tickets does not list it.", texts)


class FilesReadmeTest(unittest.TestCase):
    def test_readme_describes_the_ticket_files(self):
        text = (ROOT / "README.md").read_text()
        start = text.index("With a `.scratch/` feature")
        section = " ".join(text[start:text.index("## Install", start)].split())
        self.assertIn("`.scratch/<feature>/issues/<NN>-<slug>.md`", section)
        self.assertIn("`Status: ready-for-agent`", section)
        self.assertIn("`Blocked by:`", section)
        self.assertIn("never edits, stages or commits", section)


if __name__ == "__main__":
    unittest.main()
