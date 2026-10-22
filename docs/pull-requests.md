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

## Updating an existing PR description

1. Get the PR's diff (e.g. `gh pr diff <pr-url>`).
2. Write the description from the diff with the template above, and the
   title with the title template.
3. Update the PR (e.g. `gh pr edit <pr-url> --title … --body-file …`).
   When updating through the REST API, send `maintainer_can_modify: false`.

With the branch checked out, steps 1 and 2 go to `pr-writer` on the light
tier ([subagents.md](subagents.md#routing)); review its file before step 3.
