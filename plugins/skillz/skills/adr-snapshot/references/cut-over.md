# Cut-over

Use this once the content is audited and readers need routing to the requirements. ADRs stay where they are and stay binding throughout; see [Snapshot model and workflow impact](snapshot-model.md).

## Prepare

Search incoming references before moving anything: documentation links and anchors, agent entry points, skills, diagnostics, source comments, tests, CI and generators. Confirm that retained engineering guidance has a reachable owner. Preserve user files and follow the task's archive and deletion constraints.

Leave existing accepted ADR bodies, numbers, filenames and status relationships unchanged, apart from edits the ADR process already permits. Drafts created during this rewrite may be corrected in place as the snapshot-model reference describes. Archiving, if any, applies only to superseded non-ADR guides. The archive exists so reviewers can compare each superseded guide with its owning requirements inside the cut-over change; it is temporary, and the final report recommends deleting it (see "Recommend deleting the archive"). Choose a reversible layout, preserve original wording and line layout so each archived guide can be verified against its source (traces cite the original path at the source SHA, not the archive copy), mark the archive as history through its index or forwarding pages, and point readers to the owning requirements. Rebase relative links from each archived guide’s new directory, preserving their targets and anchors. Record that link rewrites are the only changes to the archived guide body; verify the body against its source after accounting for exactly those rewrites. Make the archive and forwarding move mechanical and replayable: drive it from a tracked script or manifest that lists each moved path, its destination and its forwarding target, and commit it alone, separate from content edits, so a stale branch can be rebuilt by replaying the move onto a fresh target instead of resolving conflicts by hand. Record in the script what it deliberately does not produce, since those edits must come from the merge.

Use forwarding pages only where existing consumers need them. Each should route to the current owner without duplicating rules. Record why a forwarding page remains and how it can eventually be removed. Any removal-check command must resolve incoming relative links (including spellings such as `../agents/x.md`) against each referring file, as well as repository-root paths, and exclude the forwarding page itself. Test that a relative incoming link blocks removal and that a page’s self-reference does not. Keep current instructions out of the guide archive. Cite every archived or forwarded source in the trace by its original path at the recorded source SHA, never by its archive path, so the evidence still resolves after the archive is deleted.

## Route readers together

- Route implementation tasks from the repository’s agent entry points to the owning requirements, with triggers for the distinct task branches. State the reading order given under "Reading order" in the snapshot-model reference. Preserve any established mirror or symlink mechanism.
- Point the ADR catalogue at the owning requirement for each topic, and add a mapping from retired vocabulary to current terms where ADRs use old words.
- Keep `CONTEXT.md` to names, definitions and `_Avoid_` entries.
- Keep the ADR workflow, and add to the repository's workflow guide that accepting an ADR updates the owning requirement and its snapshot marker in the same change, or records that the snapshot is behind. Add or update the guide's list of topics that have requirements, as the snapshot-model reference's "After the snapshot" section describes. Carry the other domain-modeling workflow changes from the snapshot-model reference. Preserve engineering conventions that still apply.
- Update skill pointers, diagnostic links and documentation-check roots or expectations affected by moved files.
- Distinguish documentation adaptations from product fixes. Keep recorded implementation defects out of the rewrite unless the user expands the scope.

Inspect every changed diff, including delegated edits. Check the whole proposed branch diff, since earlier commits can contain faults absent from the latest patch.

## Verify and deliver

Run checks against the exact cut-over tree. Confirm that no ADR body changed beyond permitted edits, compare each archived guide with its source at the target revision, not only the baseline, so a guide edited upstream after the baseline is not archived stale, resolve live and archived links and anchors, run rule-reference checks, and exercise relevant existing documentation consumers. Report missing dependencies and failed commands explicitly; a parser or link scan does not substitute for unexecuted tests.

Refresh the target revision before delivery. Reconcile relevant changes through that SHA, including ADRs accepted since the snapshot, and update the markers. Re-run the archive and forwarding script on the refreshed target rather than rebasing its output, diff the replay against the previous result, and carry any upstream edits to archived or forwarded guides into their owning requirements before archiving. Follow the repository's publishing and review workflow only within the user's authorization. A conflicting draft PR may be a useful intermediate deliverable, but report its unresolved integration and freshness limits.

Leave a durable record containing the delivered commit, target revision, snapshot markers, validation results, unresolved questions, the archive-deletion recommendation and any remaining work. Distinguish “published” from “integrated” and “audited” from “tests passed”.

## Recommend deleting the archive

The guide archive and forwarding pages are scaffolding for review, not a permanent history: git keeps every superseded guide at the recorded source SHA, and the trace cites it there. End the final report with this as the last recommended action:

- Delete the guide archive in a separate change after the cut-over merges, so reviewers keep the side-by-side comparison until then.
- Delete each forwarding page whose recorded reason for staying no longer holds: its removal check passes and no external consumer it was kept for (a wiki, generated output, published URL) still needs it. List every forwarding page that stays, with its referring files or external consumers, as the only remaining cleanup.
- Give the exact `git rm -r` paths, and the commit or SHA where the archived content can be recovered (`git show <SHA>:<original path>`).
- Confirm before recommending that no trace entry, requirement, ADR catalogue entry or agent entry point links into the archive; repoint any that do to the original path at the source SHA.

This never applies to ADRs, which stay in place and binding. Recommend by default. Delete only when the user has authorized it, and then as its own commit after the cut-over has merged, rerunning link checks on the result. The recommendation covers any guide archive or forwarding page present in the target, whichever run created it, so a refresh that archived nothing still recommends deleting an archive an earlier run left. Only when neither is present is there nothing to recommend; say so.
