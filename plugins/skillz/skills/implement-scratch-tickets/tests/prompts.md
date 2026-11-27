# Behavior cases

`implement-scratch-tickets` is started only by a person typing the command. Claude Code never loads it on its own (`disable-model-invocation: true`), and Codex never selects it implicitly (`agents/openai.yaml`). "Should activate" lists commands a person types.

## Should activate

- `/skillz:implement-scratch-tickets search-filters`: starts the workflow with `{feature: "search-filters"}`, reading `.scratch/search-filters/`.
- `/skillz:implement-scratch-tickets search-filters plan`: starts it with `{feature: "search-filters", planOnly: true}` and returns the plan without building.
- `/skillz:implement-scratch-tickets .scratch/search-filters tickets 02,03 base feat/x rounds 3`: starts it with `{feature: ".scratch/search-filters", tickets: ["02", "03"], base: "feat/x", maxFixRounds: 3}`.
- `/skillz:implement-scratch-tickets search-filters routine off`: starts it with `{feature: "search-filters", routine: false}`.
- `/skillz:implement-scratch-tickets` with no arguments in a repository with two feature directories under `.scratch/`: asks which feature to build and starts nothing until it has one. With exactly one, it uses that one and says so.

## Should not activate

- "Build the tickets in .scratch/search-filters" with no command typed: the model never starts a multi-agent run on its own.
- `/skillz:implement-tickets 56`: tickets in GitHub issues belong to implement-tickets.
- "Break this spec into tickets": writing ticket files comes before this workflow.

## Expected behavior

- In a session whose working directory is any repository, the command resolves the script from the installed skill's directory and calls the Workflow tool with that absolute `scriptPath` and `args` as a JSON object.
- If the script is missing from the skill's directory, the skill stops and names the path it checked. It never searches the working directory for a copy.
- In Codex, the skill says that workflows need Claude Code and stops.
- Only ticket files whose `Status:` is `ready-for-agent` are built, unless `tickets` names them. The run report says why each other ticket was skipped.
- A ticket whose `Blocked by:` names another ticket file branches from that ticket's branch, and its PR's base is that branch.
- Every build, review, fix and audit agent gets the ticket's full text in its prompt, so a `.scratch/` directory that git ignores still reaches agents working in a fresh worktree.
- No commit in any PR adds, changes or deletes a file under the feature directory, and the ticket files are unchanged after the run.
- Each PR body has a `Ticket: .scratch/<feature>/issues/<NN>-<slug>.md` line, restates the ticket, and gives its place in the chain, counting from the bottom. It has no `Closes #` line.
- A second run over the same feature updates the PR whose body names the ticket file instead of opening another.
- No agent in the run runs `gh stack` or follows stacking-pull-requests.
- The session never merges a PR, marks one ready, or changes a ticket file while the run is going.
