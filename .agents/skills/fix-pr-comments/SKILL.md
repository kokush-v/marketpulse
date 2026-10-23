---
name: fix-pr-comments
description: Use when fixing PR review comments one by one. Reads all unresolved review threads, shows a fix plan for each, implements the fix, then resolves the thread via GitHub API.
---

# Goal

Fix all unresolved review comments in a pull request systematically.

For each unresolved thread: show the plan, implement the fix, resolve the thread.

# Preconditions

- You must be inside a git repository with a GitHub remote.
- `gh` CLI must be authenticated.
- The current branch must have an open pull request, or the user provides a PR number.

# Workflow

## Step 1 — Identify the PR

If the user did not provide a PR number, detect it from the current branch:

```bash
gh pr view --json number,title,headRefName
```

Confirm the PR number and title with the user before proceeding.

## Step 2 — Load all unresolved review threads

Fetch review threads using the GitHub GraphQL API:

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 10) {
            nodes {
              body
              path
              line
              originalLine
              diffHunk
              author { login }
              createdAt
            }
          }
        }
      }
    }
  }
}
' -F owner=OWNER -F repo=REPO -F number=NUMBER
```

Replace OWNER, REPO, NUMBER with actual values from:

```bash
gh repo view --json owner,name
gh pr view --json number
```

Filter to threads where `isResolved: false` and `isOutdated: false`.

## Step 3 — Show the fix plan

Before making any changes, display a numbered summary of all unresolved threads:

```
Found N unresolved review threads:

1. [path/to/file.ts : line X] @reviewer
   "comment text"
   → Plan: <brief description of what will be changed>

2. [path/to/file.py : line Y] @reviewer
   "comment text"
   → Plan: <brief description of what will be changed>
```

Ask the user: "Ready to fix all N comments? Or specify numbers to skip."

## Step 4 — Fix each comment, one at a time

For each thread (in order, skipping any the user excluded):

### 4a. Announce the current fix

```
--- Fixing comment 1/N ---
File: path/to/file.ts (line X)
Comment: "comment text"
Fix: <what you're about to do>
```

### 4b. Read the relevant file context

Use view or grep to read the file around the affected line before editing.

### 4c. Implement the fix

Make targeted, minimal edits to address the comment.

Do not refactor unrelated code.

Do not change behavior outside the scope of the comment.

### 4d. Resolve the thread via GraphQL

After implementing the fix, resolve the thread using its ID:

```bash
gh api graphql -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: { threadId: $threadId }) {
    thread {
      id
      isResolved
    }
  }
}
' -F threadId=THREAD_ID
```

### 4e. Confirm resolution

Print:

```
✓ Comment 1/N resolved — thread THREAD_ID
```

Then move to the next comment.

## Step 5 — Final summary

After all threads are processed, print:

```
Done. Fixed and resolved N/N review threads.

Changed files:
- path/to/file1.ts
- path/to/file2.py

Run tests and push when ready:
  make test
  git push
```

# Rules

- Never resolve a thread before implementing its fix.
- Never skip a thread silently — either fix it or tell the user why it was skipped.
- Outdated threads (`isOutdated: true`) must be shown to the user but skipped from auto-fix unless explicitly requested.
- Do not commit changes — leave that to the user.
- Do not push changes — leave that to the user.
- If a comment is ambiguous, ask the user for clarification before fixing.
- If the file mentioned in the comment no longer exists, report it and skip.
- If a fix causes a conflict with an earlier fix in the same session, pause and explain.
- Keep each fix isolated to what the comment asks for.
- Do not add out-of-scope improvements even if you notice them.

# GraphQL helpers

## Get owner and repo

```bash
gh repo view --json owner,name --jq '"\(.owner.login) \(.name)"'
```

## Get PR number from current branch

```bash
gh pr view --json number --jq '.number'
```

## List unresolved threads (compact view)

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 1) {
            nodes { body path line author { login } }
          }
        }
      }
    }
  }
}
' -F owner=OWNER -F repo=REPO -F number=NUMBER \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)'
```

## Resolve a thread

```bash
gh api graphql -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: { threadId: $threadId }) {
    thread { id isResolved }
  }
}
' -F threadId=THREAD_ID
```
