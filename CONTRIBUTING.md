# Contributing

## How do I... <a name="toc"></a>

* [Use This Guide](#introduction)?
* Ask or Say Something?
  * [Request Support](#request-support)
  * [Report an Error or Bug](#report-an-error-or-bug)
  * [Report a security concern](#report-a-security-concern)
  * [Request a Feature](#request-a-feature)
* Make Something?
  * [Submitting a Pull Request](#submitting-a-pull-request)
  * [Project Setup](#project-setup)
  * [Contribute Documentation](#contribute-documentation)
  * [Contribute Code](#contribute-code)
* Manage Something
  * [Provide Support on Issues](#provide-support-on-issues)
  * [Label Issues](#label-issues)
  * [Clean Up Issues and PRs](#clean-up-issues-and-prs)
  * [Review Pull Requests](#review-pull-requests)
  * [Merge Pull Requests](#merge-pull-requests)
  * [Tag a Release](#tag-a-release)
  * [Join the Project Team](#join-the-project-team)
* Add a Guide Like This One [To My Project](#attribution)?


## Introduction

Thank you for your interest in contributing! All types of contributions are encouraged and valued. See the [table of contents](#toc) for different ways to help and details about how this project handles them.

Please make sure to read the relevant section before making your contribution. It will make it a lot easier for project maintainers to make the most of it and smooth out the experience for all involved.

The [Project Team](#join-the-project-team) looks forward to your contributions.

## Request Support

If you have a question about this project, how to use it, or just need clarification about something:

* Open an Issue at https://github.com/natlas/natlas/issues
* Provide as much context as you can about what you're running into
* Provide project and platform versions (NATLAS_VERSION, OS version, etc), depending on what seems relevant. If not, please be prepared to provide this information upon further inquiry.

Once the issue is filed:

* The project team will [label the issue](#label-issues).
* Someone will try to respond as soon as possible.
* If you or the maintainers don't respond to an issue for 30 days, the [issue may be closed](#clean-up-issues-and-prs). If you want to come back to it, reply to the issue and we will reopen it. Please avoid creating a new issue as an extension of one you've already made.

## Report an Error or Bug

If you run into an error or bug with the project:

* Open an Issue at https://github.com/natlas/natlas/issues
* Provide *reproduction steps* that someone else can follow to recreate the bug or error on their own.
* Provide project and platform versions (NATLAS_VERSION, OS version, commit hash, etc), depending on what seems relevant. If not, please be prepared to provide this information when asked for it.

Once the issue is filed:

* The project team will [label the issue](#label-issues).
* A team member will try to reproduce the issue with your provided steps. If there are no repro steps or no obvious way to reproduce the issue, the team will ask you for those steps and mark the issue as `needs-repro`. Bugs with the `needs-repro` tag will not be addressed until they are reproduced.
* If the team is able to reproduce the issue, it will be marked `needs-fix`, as well as any other tags that are relevant (such as `agent` or `server`), and the issue will be left to be [implemented by someone](#contribute-code).
* If you or the maintainers don't respond to an issue for 30 days, the [issue may be closed](#clean-up-issues-and-prs). If you want to come back to it, reply to the issue and we will reopenit. Please avoid creating a new issue as an extension of one you've already made.

## Request a Feature

If the project doesn't do something you need or want it to do:

* Open an Issue at https://github.com/natlas/natlas/issues
* Provide as much context as you can about what you'd like it to do.
* Please try and be clear about why existing features and alternatives would not work for you.

Once it's filed:

* The project team will [label the issue](#label-issues).
* The project team will evaluate the feature request, possibly asking you more questions to understand its purpose and any relevant requirements. If the issue is closed, the team will convey their reasoning and suggest an alternative path forward.
* If the feature request is accepted, it will be marked for implementation by being assigned a milestone, which can then be done by either by a core team member or by anyone in the community who wants to [contribute code](#contribute-code).

Note: The team is unlikely to be able to accept every single feature request that is filed. Please understand if they need to say no.

## Submitting a Pull Request

This project refrains from, or attempts to refrain from, making any commits to master unless as part of a version release cycle. Therefore, any pull requests that are submitted should be targeted against the latest development branch. That is currently the `v0.6.x` branch, which supports natlas versions beginning with `0.6`. Any pull request submitted against master will almost certainly be asked to retarget to the development branch.

## Project Setup

So you wanna contribute some code! That's great! This project uses [GitHub Pull Requests](#submitting-a-pull-request) to manage outside contributions, so [read up on how to fork a GitHub project and file a PR](https://guides.github.com/activities/forking) if you've never done it before.

If this seems like a lot or you aren't able to do all this setup, you might also be able to [edit the files directly](https://help.github.com/articles/editing-files-in-another-user-s-repository/) without having to do any of this setup. Yes, [even code](#contribute-code).

If you want to go the usual route and run the project locally, though:

* Be using an ubuntu-based development environment
* [Fork the project](https://guides.github.com/activities/forking/#fork)

Then in your terminal:
* `cd path/to/clone/natlas-server`
* `sudo ./setup-server.sh`
* `sudo ./setup-elastich.sh`
* `cd ../natlas-agent`
* `sudo ./setup-agent.sh`

This should setup the environment necessary to develop and test code for both the `natlas-server` and the `natlas-agent`.

## Contribute Documentation

Documentation is a super important, critical part of this project. Docs are how we keep track of what we're doing, how, and why. It's how we stay on the same page about our policies. And it's how we tell others everything they need in order to be able to use this project -- or contribute to it. So thank you in advance.

Documentation contributions of any size are welcome! Feel free to [file a PR](#submitting-a-pull-request) even if you're just rewording a sentence to be more clear, or fixing a spelling mistake!

To contribute documentation:

* [Set up the project](#project-setup).
* Edit or add any relevant documentation.
* Make sure your changes are formatted correctly and consistently with the rest of the documentation.
* Re-read what you wrote, and run a spellchecker on it to make sure you didn't miss anything.
* Write clear, concise commit message(s).
* Go to https://github.com/natlas/natlas/pulls and open a [new pull request](#submitting-a-pull-request) with your changes.
* If your PR is connected to an open issue, add a line in your PR's description that says `Fixes: #123`, where `#123` is the number of the issue you're fixing.

Once you've filed the PR:

* One or more maintainers will use GitHub's review feature to review your PR.
* If the maintainer asks for any changes, edit your changes, push, and ask for another review.
* If the maintainer decides to pass on your PR, they will thank you for the contribution and explain why they won't be accepting the changes. That's ok! We still really appreciate you taking the time to do it, and we don't take that lightly.
* If your PR gets accepted, it will be marked as such, and merged into the latest development branch soon after. Your contribution will be distributed to the masses next time the maintainers [tag a release](#tag-a-release)

## Contribute Code

We like code commits a lot! They're super handy, and they keep the project going and doing the work it needs to do to be useful to others.

Code contributions of just about any size are acceptable!

To contribute code:

* [Set up the project](#project-setup).
* Make any necessary changes to the source code.
* Include any [additional documentation](#contribute-documentation) the changes might need.
* Write or show tests that verify that your contribution works as expected.
* Write clear, concise commit message(s).
* Go to https://github.com/natlas/natlas/pulls and open a [new pull request](#submitting-a-pull-request) with your changes.
* If your PR is connected to an open issue, add a line in your PR's description that says `Fixes: #123`, where `#123` is the number of the issue you're fixing.

Once you've filed the PR:

* One or more maintainers will use GitHub's review feature to review your PR.
* If the maintainer asks for any changes, edit your changes, push, and ask for another review. Additional tags will be added depending on the review.
* If the maintainer decides to pass on your PR, they will thank you for the contribution and explain why they won't be accepting the changes. That's ok! We still really appreciate you taking the time to do it, and we don't take that lightly.
* If your PR gets accepted, it will be marked as such, and merged into the latest development branch soon after. Your contribution will be distributed to the masses next time the maintainers [tag a release](#tag-a-release).

## Provide Support on Issues

[Needs Collaborator](#join-the-project-team): none

Helping out other users with their questions is a really awesome way of contributing to any community. It's not uncommon for most of the issues on an open source projects being support-related questions by users trying to understand something they ran into, or find their way around a known bug.

Sometimes, the `support` label will be added to things that turn out to actually be other things, like bugs or feature requests. In that case, suss out the details with the person who filed the original issue, add a comment explaining what the bug is, and change the label from `support` to `bug` or `enhancement`. If you can't do this yourself, @mention a maintainer so they can do it.

In order to help other folks out with their questions:

* Go to the issue tracker and [filter open issues by the `support` label](https://github.com/natlas/natlas/issues?q=is%3Aopen+is%3Aissue+label%3Asupport).
* Read through the list until you find something that you're familiar enough with to give an answer to.
* Respond to the issue with whatever details are needed to clarify the question, or get more details about what's going on.
* Once the discussion wraps up and things are clarified, either close the issue, or ask the original issue filer (or a maintainer) to close it for you.

Some notes on picking up support issues:

* Avoid responding to issues you don't know you can answer accurately.
* As much as possible, try to refer to past issues with accepted answers. Link to them from your replies with the `#123` format.
* Be kind and patient with users -- often, folks who have run into confusing things might be upset or impatient. This is ok. Try to understand where they're coming from, and if you're too uncomfortable with the tone, feel free to stay away or withdraw from the issue. (note: if the user is outright hostile or is violating the CoC, [refer to the Code of Conduct](CODE_OF_CONDUCT.md) to resolve the conflict).

## Label Issues

[Needs Collaborator](#join-the-project-team): Issue Tracker

One of the most important tasks in handling issues is labeling them usefully and accurately. All other tasks involving issues ultimately rely on the issue being classified in such a way that relevant parties looking to do their own tasks can find them quickly and easily.

In order to label issues, [open up the list of unlabeled issues](https://github.com/natlas/natlas/issues?q=is%3Aopen+is%3Aissue+no%3Alabel) and, **from newest to oldest**, read through each one and apply issue labels according to the table below. If you're unsure about what label to apply, skip the issue and try the next one: don't feel obligated to label each and every issue yourself!

Label | Apply When | Notes
--- | --- | ---
`agent` | Applies to issues or pull requests that affect natlas-agent code. |
`bug` | Cases where the code (or documentation) is behaving in a way it wasn't intended to. | If something is happening that surprises the *user* but does not go against the way the code is designed, it should use the `enhancement` label.
`critical` | Added to `bug` issues if the problem described makes the code completely unusable in a common situation. |
`dependencies` | Added to pull requests that update a dependency file. | Most commonly done to bump versions for security fixes.
`documentation` | Added to issues or pull requests that affect any of the documentation for the project. | Can be combined with other labels, such as `bug` or `enhancement`.
`duplicate` | Added to issues or PRs that refer to the exact same issue as another one that's been previously labeled. | Duplicate issues should be marked and closed right away, with a message referencing the issue it's a duplicate of (with `#123`)
`enhancement` | Added to [feature requests](#request-a-feature), PRs, or documentation issues that are purely additive: the code or docs currently work as expected, but a change is being requested or suggested. |
`help wanted` | Applied by [Committers](#join-the-project-team) to issues and PRs that they would like to get outside help for. Generally, this means it's lower priority for the maintainer team to itself implement, but that the community is encouraged to pick up if they so desire | Never applied on first-pass labeling.
`in-progress` | Applied by [Committers](#join-the-project-team) to PRs that are pending some work before they're ready for review. | The original PR submitter should @mention the team member that applied the label once the PR is complete.
`invalid` | Applied to issues or PRs that don't seem right for one reason or another. |
`performance` | This issue or PR is directly related to improving performance. |
`refactor` | Added to issues or PRs that deal with cleaning up or modifying the project for the betterment of it. |
`security` | Applies to issues or PRs that deal with the security of the project. |
`server` | Applies to issues or pull requests that affect natlas-server code |
`starter` | Applied by [Committers](#join-the-project-team) to issues that they consider good introductions to the project for people who have not contributed before. These are not necessarily "easy", but rather focused around how much context is necessary in order to understand what needs to be done for this project in particular. | Existing project members are expected to stay away from these unless they increase in priority.
`support` | This issue is either asking a question about how to use the project, clarifying the reason for unexpected behavior, or possibly reporting a `bug` but does not have enough detail yet to determine whether it would count as such. | The label should be switched to `bug` if reliable reproduction steps are provided. Issues primarily with unintended configurations of a user's environment are not considered bugs, even if they cause crashes.
`wontfix` | Labelers may apply this label to issues that clearly have nothing at all to do with the project or are otherwise entirely outside of its scope/sphere of influence. [Committers](#join-the-project-team) may apply this label and close an issue or PR if they decide to pass on an otherwise relevant issue. | The issue or PR should be closed as soon as the label is applied, and a clear explanation provided of why the label was used. Contributors are free to contest the labeling, but the decision ultimately falls on committers as to whether to accept something or not.

## Clean Up Issues and PRs

[Needs Collaborator](#join-the-project-team): Issue Tracker

Issues and PRs can go stale after a while. Maybe they're abandoned. Maybe the team will just plain not have time to address them any time soon.

In these cases, they should be closed until they're brought up again or the interaction starts over.

To clean up issues and PRs:

* Search the issue tracker for issues or PRs, and add the term `updated:<=YYYY-MM-DD`, where the date is 30 days before today.
* Go through each issue *from oldest to newest*, and close them if **all of the following are true**:
  * not opened by a maintainer
  * not marked as `critical`
  * not marked as `starter` or `help wanted` (these might stick around for a while, in general, as they're intended to be available)
  * no explicit messages in the comments asking for it to be left open
  * does not belong to a milestone
* Leave a message when closing saying "Cleaning up stale issue. Please reopen or ping us if and when you're ready to resume this. See https://github.com/natlas/natlas/blob/master/CONTRIBUTING.md#clean-up-issues-and-prs for more details."

## Review Pull Requests

[Needs Collaborator](#join-the-project-team): Issue Tracker

While anyone can comment on a PR, add feedback, etc, PRs are only *approved* by team members with Issue Tracker or higher permissions.

PR reviews use [GitHub's own review feature](https://help.github.com/articles/about-pull-request-reviews/), which manages comments, approval, and review iteration.

Some notes:

* You may ask for minor changes ("nitpicks"), but consider whether they are really blockers to merging: try to err on the side of "approve, with comments".
* Please make sure you're familiar with the code or documentation being updated, unless it's a minor change (spellchecking, minor formatting, etc). You may @mention another project member who you think is better suited for the review, but still provide a non-approving review of your own.
* Be extra kind: people who submit code/doc contributions are putting themselves in a pretty vulnerable position, and have put time and care into what they've done (even if that's not obvious to you!) -- always respond with respect, be understanding, but don't feel like you need to sacrifice your standards for their sake, either. Just don't be a jerk about it, okay?

## Merge Pull Requests

[Needs Collaborator](#join-the-project-team): Committer

Team members who can commit to the project are able to merge pull requests that have been reviewed and marked as approved. Please ensure that the pull request is targeting the latest version branch as defined in the instructions on [submitting a pull request](#submitting-a-pull-request). At this point, you should attempt to merge the pull request in the following order:

1. If you can rebase the commits to the version branch, do so.
1. If you cannot rebase the commits, please create a merge commit to the version branch.
1. Under certain circumstances you may wish to squash and merge, but this should always be discussed with another maintainer if possible.

## Tag A Release

[Needs Collaborator](#join-the-project-team): Committer

Tagging a natlas release has been mostly automated using the `release.sh` script in the base of the repository. This script should be run from the version branch that you're currently developing on. It will walk you through the release process. It is important to note that the `CHANGELOG.md` file must be updated, accurate, and committed to the branch prior to running the release script. It will prompt you to double check that you've done this. Make sure to update the `Unreleased` section to your new target version and then add a new `Unreleased` header above your target version.

Once the `CHANGELOG.md` has been updated and committed, the release script will identify the current version as defined in `natlas-agent/config.py` and `natlas-server/config.py`. If these versions do not match for whatever reason, the script will error out. You should correct this manually. After the current version is detected, it will prompt you to provide the next version. You should follow [semver](https://semver.org/) as much as possible when doing this. Furthermore, releases from a given version branch should only be tagged with matching versions.

Once the version is selected, the script will ask you to confirm that you're ready to release. If everything is good, go ahead and hit `y`. It will give you a minute to cancel before it commits the version changes to the respective config files and then tags and pushes the release. After it has tagged and pushed the release, it will automatically copy the `LICENSE` and `CHANGELOG.md` files into the `natlas-server/` and `natlas-agent/` folders and then proceed to create a tarball of the respective components. Double check that these tarballs do not include any unwanted files (such as the contents of data directories, log directories, development files, etc) and then upload them to the releases page on github. Copy the relevant section of the `CHANGELOG.md` file into the releases page description for the given version, give it a title that briefly summarizes the release, and then save the release.


## Join the Project Team

### Ways to Join

There are many ways to contribute! Most of them don't require any official status unless otherwise noted. That said, there's a couple of positions that grant special repository abilities, and this section describes how they're granted and what they do.

All of the below positions are granted based on the project team's needs, as well as their consensus opinion about whether they would like to work with the person and think that they would fit well into that position. The process is relatively informal, and it's likely that people who express interest in participating can just be granted the permissions they'd like.

You can spot a collaborator on the repo by looking for the `[Collaborator]` or `[Owner]` tags next to their names.

Permission | Description
--- | ---
Issue Tracker | Granted to contributors who express a strong interest in spending time on the project's issue tracker. These tasks are mainly [labeling issues](#label-issues), [cleaning up old ones](#clean-up-issues-and-prs), and [reviewing pull requests](#review-pull-requests), as well as all the usual things non-team-member contributors can do. Issue handlers should not merge pull requests, tag releases, or directly commit code themselves: that should still be done through the usual pull request process. Becoming an Issue Handler means the project team trusts you to understand enough of the team's process and context to implement it on the issue tracker.
Committer | Granted to contributors who want to handle the actual pull request merges, tagging new versions, etc. Committers should have a good level of familiarity with the codebase, and enough context to understand the implications of various changes, as well as a good sense of the will and expectations of the project team.
Admin/Owner | Granted to people ultimately responsible for the project, its community, etc.

## Attribution

This guide was created based on the WeAllJS `CONTRIBUTING.md` generator. [Make your own](https://github.com/WeAllJS/weallcontribute)!