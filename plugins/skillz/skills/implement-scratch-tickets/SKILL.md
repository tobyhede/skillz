---
name: implement-scratch-tickets
description: Runs the implement-scratch-tickets workflow, which builds a feature's ready-for-agent ticket files from a .scratch feature directory into a chain of draft PRs, reviews and fixes them, and writes a run report. The implement-tickets workflow for tickets kept as markdown files in the repository instead of an issue tracker. Claude Code only. Started by the person, never by the model.
argument-hint: "<feature> [plan] [tickets 01,03] [base <branch>] [rounds <n>] [routine on|off]"
disable-model-invocation: true
---

# implement-scratch-tickets

Start the `implement-scratch-tickets` workflow in this skill's `workflows/implement-scratch-tickets.js`. The person typing this command is their opt-in to a multi-agent run. The Workflow tool does the work. This session does not.

This runs in Claude Code only. Codex cannot run workflows. In Codex, say that and stop.

The tickets are markdown files in the repository, laid out as the mattpocock-skills local tracker and its `to-tickets` skill write them:

- `.scratch/<feature>/spec.md` is the spec. It is optional.
- `.scratch/<feature>/issues/<NN>-<slug>.md` is one ticket per file, numbered from `01`. A ticket's id is its `NN`.
- Each ticket has a `Status:` line, and `ready-for-agent` marks it buildable. A status of `done`, `resolved`, `closed` or `wontfix` closes it.
- Each ticket has a `Blocked by:` line naming the numbers or titles of the tickets that gate it, or `None`.

The run reads these files but never edits, stages or commits them. Each PR names its ticket on a `Ticket: <path>` line, which is how a later run finds and updates it.

1. Find the script. It ships with this skill, at `${CLAUDE_SKILL_DIR}/workflows/implement-scratch-tickets.js`. Claude Code fills in `${CLAUDE_SKILL_DIR}` with this skill's installed directory, which is also the "Base directory for this skill" shown when it loads. Never look for it in the working directory or its git checkout. If the file is not there, stop and say which path you checked.
2. Build `args` from the command's arguments:
   - a bare word or path that is not a keyword below is `feature`: a slug under `.scratch/` or a directory path;
   - `plan` sets `planOnly: true`;
   - `tickets 01,03` sets `tickets: ["01", "03"]`;
   - `base <branch>` sets `base`;
   - `rounds <n>` sets `maxFixRounds`;
   - `routine on` or `routine off` sets `routine` to true or false. Leave it out to let the run check for `.github/workflows/claude-review.yml`.

   With no feature, list the directories under `.scratch/` that hold an `issues/` directory. If there is exactly one, use it and say so. Otherwise ask which feature to build, and start nothing until you have one. Pass `args` as a JSON object, not a string.
3. Call the Workflow tool with `scriptPath` set to the script's absolute path and `args`. Say in one line that it has started, and what it will build.
4. When it finishes, give the person its run report. List each PR it opened or updated, with its ticket file, its place in the chain, CI state, and open findings.

Never merge a PR, mark one ready, or change a ticket file while the run is going. The workflow's own rules apply to every agent it starts.
