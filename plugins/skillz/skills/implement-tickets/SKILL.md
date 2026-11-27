---
name: implement-tickets
description: Runs the implement-tickets workflow, which builds a spec's ready-for-agent tickets into a chain of draft PRs, reviews and fixes them, and writes a run report. Works with tickets in GitHub issues or in .scratch markdown files in the repository, picking whichever the project uses. Claude Code only. Started by the person, never by the model.
argument-hint: "<spec issue number | .scratch feature> [plan] [tickets 12,13] [base <branch>] [rounds <n>] [routine on|off]"
disable-model-invocation: true
---

# implement-tickets

Start the `implement-tickets` workflow in this skill's `workflows/implement-tickets.js`. The person typing this command is their opt-in to a multi-agent run. The Workflow tool does the work. This session does not.

This runs in Claude Code only. Codex cannot run workflows. In Codex, say that and stop.

## Where the tickets are

The workflow reads tickets from one of two trackers:

- **GitHub** (`tracker: "github"`): a spec issue whose sub-issues carry the `ready-for-agent` label, blocked by GitHub's issue dependencies or `Blocked by: #n` lines. Each PR closes its issue.
- **Files** (`tracker: "files"`): markdown files in the repository, laid out as the mattpocock-skills local tracker and its `to-tickets` skill write them. `.scratch/<feature>/spec.md` is the spec, and is optional. `.scratch/<feature>/issues/<NN>-<slug>.md` is one ticket per file, with a `Status:` line (`ready-for-agent` to build; `done`, `resolved`, `closed` or `wontfix` to close it) and a `Blocked by:` line naming the tickets that gate it, or `None`. A ticket's id is its `NN`. The run reads these files but never edits, stages or commits them, and each PR names its ticket on a `Ticket: <path>` line instead of closing an issue.

## Steps

1. Find the script. It ships with this skill, at `${CLAUDE_SKILL_DIR}/workflows/implement-tickets.js`. Claude Code fills in `${CLAUDE_SKILL_DIR}` with this skill's installed directory, which is also the "Base directory for this skill" shown when it loads. Never look for it in the working directory or its git checkout. If the file is not there, stop and say which path you checked.
2. Build `args` from the command's arguments:
   - a bare number is `spec`, a GitHub spec issue;
   - a bare word or path that is not a number or a keyword below is `feature`, a slug under `.scratch/` or a directory path, and means ticket files;
   - `plan` sets `planOnly: true`;
   - `tickets 12,13` sets `tickets: [12, 13]`; with a feature, `tickets 01,03` sets `tickets: ["01", "03"]`;
   - `base <branch>` sets `base`;
   - `rounds <n>` sets `maxFixRounds`;
   - `routine on` or `routine off` sets `routine` to true or false. Leave it out to let the run check for `.github/workflows/claude-review.yml`.

   The script picks the tracker from these: `feature` means files, otherwise GitHub. Pass `args` as a JSON object, not a string.
3. With no spec, feature or tickets, work out which tracker the project uses:
   - If `docs/agents/issue-tracker.md` exists, follow it: it names the tracker the mattpocock-skills setup chose.
   - Otherwise, if `.scratch/` holds feature directories with an `issues/` directory, the project uses files.
   - Otherwise it uses GitHub.

   For files, list the feature directories under `.scratch/` that hold an `issues/` directory. If there is exactly one, use it and say so; otherwise ask which feature to build. For GitHub, ask for the spec issue number. Start nothing until you have one.
4. Call the Workflow tool with `scriptPath` set to the script's absolute path and `args`. Say in one line that it has started, which tracker it reads, and what it will build.
5. When it finishes, give the person its run report. List each PR it opened or updated, with its ticket, its place in the chain, CI state, and open findings.

Never merge a PR, mark one ready, or change its tickets while the run is going. The workflow's own rules apply to every agent it starts.
