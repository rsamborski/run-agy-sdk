# AGY SDK GitHub Action

`run-agy-sdk` is a composite GitHub Action demonstrating how to run the Antigravity Python SDK (`google-antigravity`) for automated code reviews and task execution. Because it is a composite action running directly on the host, it allows the SDK to spawn hardened Docker-based MCP servers (such as `github-mcp-server`) on the runner.

> [!WARNING]
> **Ephemeral, Isolated Runners Only:** Because `run-agy-sdk` executes on the runner host and talks to `/var/run/docker.sock`, it **must only run on ephemeral, single-use VMs** (such as GitHub-hosted `ubuntu-latest` runners or ephemeral VM autoscalers). **Never** run this action on persistent or shared self-hosted runners.

## ⚙️ Workflow Installation & Setup

To use `run-agy-sdk` in another repository, configure a GitHub Actions workflow pinned to full 40-character commit SHAs.

### 1. Provision API Key Secrets

The Antigravity action requires a Gemini API key to authenticate language model interactions.

1. Generate a Gemini API key in [Google AI Studio](https://aistudio.google.com/app/api-keys).
2. In your target repository, go to **Settings** > **Secrets and variables** > **Actions**.
3. Create a new repository secret named `GEMINI_API_KEY` and paste your API key as the value.

> [!CAUTION]
> **Dependabot Secrets Trade-off:** Workflows triggered by Dependabot cannot read standard **Actions** secrets unless the secret is also added under **Settings** > **Secrets and variables** > **Dependabot**. Be aware that enabling AI reviews on Dependabot PRs exposes your API quota and PR-commenting `GITHUB_TOKEN` to untrusted upstream dependency diffs and release notes—only add `GEMINI_API_KEY` to Dependabot secrets if you accept that risk.

### 2. Configure the GitHub Actions Workflow

Create a new file in your repository at `.github/workflows/antigravity-review.yml` and copy the following SHA-pinned configuration:

```yaml
name: '🔎 Antigravity PR Review'

on:
  pull_request:
    types: [opened, reopened]
  workflow_dispatch: # Allows manual trigger from the Actions tab

concurrency:
  group: '${{ github.workflow }}-${{ github.event.pull_request.number || github.ref_name }}'
  cancel-in-progress: true

jobs:
  antigravity-review:
    runs-on: 'ubuntu-latest'
    if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository
    timeout-minutes: 20

    # Minimal permissions required to read contents and post PR review feedback
    permissions:
      contents: 'read'
      pull-requests: 'write'

    steps:
      - name: 'Checkout Repository'
        uses: 'actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1' # v7.0.1
        with:
          persist-credentials: false

      - name: 'Run Antigravity PR Review'
        # Pin to a full 40-character commit SHA (or signed release SHA)
        uses: 'rsamborski/run-agy-sdk@0634f555fdf93cc230321689a9f0d85ccfdcc368'
        id: 'agy_pr_review'
        with:
          api-key: '${{ secrets.GEMINI_API_KEY }}'
          github-token: '${{ github.token }}'
          mode: 'review'
          prompt: '/antigravity-review'
          trust-workspace: 'false'
          sandbox-profile: 'true'
          # Set to 'false' on sensitive private repositories to suppress stdout transcript streaming
          stream-output: 'true'
```

> [!IMPORTANT]
> When reviewing untrusted external fork PRs (for example via comment-triggered `issue_comment` workflows), keep `trust-workspace: 'false'`, never execute code from the untrusted PR checkout, and check out the PR into an isolated subdirectory passed via `workspace-dir` (see [.github/workflows/antigravity-review.yml](.github/workflows/antigravity-review.yml)).

For a complete workflow template that supports both **Automated PR Auditing** and **Comment-Triggered Reviews** (`@agy /review`), refer to [.github/workflows/antigravity-autonomous-review.yml](.github/workflows/antigravity-autonomous-review.yml).

## 🔒 Security & Repository Governance Checklist

Apply the following GitHub repository/organization settings alongside the workflow controls above:

- **Default `GITHUB_TOKEN` Permissions** (**Settings** > **Actions** > **General**): Set to **Read repository contents and packages permissions**, and keep *"Allow GitHub Actions to create and approve pull requests"* **unchecked**.
- **Prefer `GITHUB_TOKEN` Over GitHub App Tokens**: Default to `github.token` (`GITHUB_TOKEN` cannot approve PRs). If a GitHub App token is explicitly opted into (`USE_GITHUB_APP_TOKEN=true`), exclude the App from branch-protection approval rules so prompt injection cannot satisfy required review counts.
- **Outside Collaborator Fork Approvals**: Set *"Fork pull request workflows from outside collaborators"* to **Require approval for all outside collaborators**.
- **Branch & Tag Rulesets + `CODEOWNERS`**: Protect `main` and `v*` release tags with rulesets; require `CODEOWNERS` review on `.github/`, `action.yml`, `run_agent.py`, and `requirements.txt`; grant external collaborators read-only access unless write access is strictly needed.
- **Environment Gates & Credential Hygiene**: Gate `mode: 'goal'` / `trust-workspace: 'true'` workflows behind a protected GitHub Environment with required human reviewers, set `stream-output: 'false'` on sensitive private repos, and rotate static `GEMINI_API_KEY` / `APP_PRIVATE_KEY` secrets periodically.

## 🤝 Acknowledgments

This project is inspired by [run-gemini-cli](https://github.com/google-github-actions/run-gemini-cli).

## 📄 License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for the full license text.

## 📝 NOTE

This is not an officially supported Google product.
