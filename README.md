# AGY SDK GitHub Action

`run-agy-sdk` is a composite GitHub Action demonstrating how to run the Antigravity Python SDK (`google-antigravity`) for automated code reviews and task execution. Because it is a composite action running directly on the host, it allows the SDK to spawn Docker-based MCP servers (such as `github-mcp-server`) directly on the host runner.

## ⚙️ Workflow Installation & Setup

To use `run-agy-sdk` in another repository, you need to configure a GitHub Actions workflow that references this action. Follow the instructions below to set up automated reviews or comment-based on-demand reviews.

### 1. Provision API Key Secrets

The Antigravity action requires a Gemini API key to authenticate language model interactions.

1. Generate a Gemini API key in [Google AI Studio](https://aistudio.google.com/app/api-keys).
2. In your target repository, go to **Settings** > **Secrets and variables** > **Actions**.
3. Create a new repository secret named `GEMINI_API_KEY` and paste your API key as the value.
4. *(Optional)* If you use Dependabot and want workflows to run on Dependabot pull requests, also go to **Settings** > **Secrets and variables** > **Dependabot** and add `GEMINI_API_KEY` there (workflows triggered by Dependabot cannot access **Actions** secrets).

### 2. Configure the GitHub Actions Workflow

Create a new file in your repository at `.github/workflows/antigravity-review.yml` and copy the following configuration:

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
    timeout-minutes: 20
    
    # Required permissions for the action to read contents and post PR comments/feedback
    permissions:
      contents: 'read'
      pull-requests: 'write'
      issues: 'write'

    steps:
      - name: 'Checkout Repository'
        uses: 'actions/checkout@v6'
        with:
          persist-credentials: false

      - name: 'Run Antigravity PR Review'
        # Reference this action remotely from its repository
        uses: 'rsamborski/run-agy-sdk@main'
        id: 'agy_pr_review'
        with:
          api-key: '${{ secrets.GEMINI_API_KEY }}'
          github-token: '${{ secrets.GITHUB_TOKEN || github.token }}'
          mode: 'review'
          prompt: '/antigravity-review'
          trust-workspace: 'true'
          sandbox-profile: 'true'
```

> [!TIP]
> For production environments, it is recommended to lock the action version to a specific commit SHA (e.g., `rsamborski/run-agy-sdk@<commit-sha>`) rather than `@main` to prevent unexpected breaks from upstream updates.

For a complete workflow template that supports both **Automated PR Auditing** (runs automatically on code updates) and **Comment-Triggered Reviews** (triggered via PR comments), please refer to the reference workflow in [.github/workflows/antigravity-autonomous-review.yml](.github/workflows/antigravity-autonomous-review.yml).

## 🤝 Acknowledgments

This project is inspired by [run-gemini-cli](https://github.com/google-github-actions/run-gemini-cli).

## 📄 License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for the full license text.

## 📝 NOTE

This is not an officially supported Google product.