# Pull requests

Conventions for Ynput pull requests opened from any repository in this
workspace.

## Title

```text
[YN-####]: <short label>
```

`YN-####` is the related support ticket. Keep the label short.

## Description template

Write from the **user's** point of view: a very brief, easy-to-read summary
of the product change and why it was needed. Keep it executive-level and
short.

```markdown
## Changelog Description
<!-- User-perspective summary of the product change and the reasons for it.
     What problem does it solve? -->

## Additional info
<!-- Very brief technical context or code examples, only if useful. -->

## Testing notes:
<!-- Steps a reviewer can follow to verify the change, e.g.
1. start with this step
2. follow this step
-->

## Dependency
Close <Issue-url>

## Related support tickets
[<YN-####>](<Support-url>)
```

Drop a section that has nothing to say (e.g. no dependency). Testing notes
must describe manual host-application steps where an agent could not run
them ([constitution Article 8](ayon/constitution.md#article-8--the-verification-ladder-depends-on-what-the-repo-has)).
Never name or describe a private repository or client material in a PR
([Article 9](ayon/constitution.md#article-9--private-repositories-are-non-referenceable)).

## Draft, cross-review, human review

Every new pull request, in any repository of this workspace, follows this
order. Nothing is skipped because the change is small.

1. **Open it as a draft** (`gh pr create --draft`; a stack: every layer
   draft). Never open a PR ready for review.
2. **Cross-review by another agent**, right after the PR exists. The
   reviewer is a fresh agent that did not write the change: it gets the PR
   link, the base ref and the workspace root, never the author's
   conclusions or a list of what to check. It is critical on purpose: it
   looks for bugs, broken contracts, missed host differences, gaps in the
   tests and anything the description claims but the code does not do. It
   runs the [review checks](ayon/review-checks.md) too (`diff-reviewer`).
   A real defect or a design doubt on a deep question goes to a
   general-purpose agent on the deep tier
   ([subagents.md](subagents.md#routing)).
3. **Exchange between reviewer and author.** The reviewer posts its
   findings on the PR (one comment per finding, `path:line`, why it is
   wrong, a failing input where it has one). The author agent answers each
   finding on the PR: fixed in `<commit>`, or not changed with the reason.
   The reviewer then re-checks the answers and the new commits. Two rounds
   at most; a finding still open after that is left for the user and named
   in the PR description. The author verifies a finding before acting on
   it: a reviewer's report is a claim like any subagent's.
4. **Human review.** Only after step 3 is the user asked to review. The
   user reads the PR with the findings and answers already on it and marks
   it ready for review themselves.
5. **Merge.** An agent merges a PR only when it is no longer a draft, and
   only on the user's explicit go-ahead. A draft PR is never merged, never
   marked ready by an agent, and its checks and approvals do not change
   that.

This applies to new PRs from now on; PRs opened before the rule keep the
state they have.

## Updating an existing PR description

1. Get the PR's diff (e.g. `gh pr diff <pr-url>`).
2. Write the description from the diff with the template above, and the
   title with the title template.
3. Update the PR (e.g. `gh pr edit <pr-url> --title … --body-file …`).
   When updating through the REST API, send `maintainer_can_modify: false`.

With the branch checked out, steps 1 and 2 go to `pr-writer` on the light
tier ([subagents.md](subagents.md#routing)); review its file before step 3.
