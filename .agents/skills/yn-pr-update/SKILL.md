---
name: yn-pr-update
description: Updating Ynput PullRequest
disable-model-invocation: true
---

update github pullrequest description <pr-url>. 
- Be very brief at executive level style
- Get diff from the PullRequest 
- Use [@yn-pr-description](../yn-pr-description/SKILL.md)  template for description. 
- Update the pull request, 'maintainer_can_modify' in updating request is set to False.
- Update title as well with this template: `[<YN-####>]: <!-- Generate short label -->`.
