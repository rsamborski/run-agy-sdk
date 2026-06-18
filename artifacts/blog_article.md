---
title: "Building an agentic PR reviewer with Antigravity SDK | run-agy-sdk"
description: "Prepare for the June 2026 transition from Gemini CLI by migrating your automated PR review pipelines to the Antigravity SDK."
keywords: ["Antigravity CLI migration", "run-agy-sdk", "Antigravity SDK", "GitHub Action code review", "Gemini CLI deprecation"]
---

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "Migrating to Antigravity SDK for Automated PR Reviews",
  "description": "Prepare for the June 2026 transition from Gemini CLI by migrating your automated PR review pipelines to the Antigravity SDK.",
  "inLanguage": "en",
  "author": {
    "@type": "Person",
    "name": "Developer Advocate"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Google Cloud"
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://github.com/rsamborski/run-agy-sdk"
  }
}
</script>

# Building an agentic PR reviewer with Antigravity SDK

![Blog Hero Image](artifacts/blog_hero_image_medium.png)

As announced in yesterday's [blog post](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/), Gemini CLI and Gemini Code Assist IDE extensions stopped serving requests for Google AI Pro and Ultra, as well as those using it free of charge using Gemini Code Assist for individuals. Google has unified its AI terminal tools by transitioning the community-focused Gemini CLI into Antigravity CLI, a new agent-first platform built for complex, multi-agent workflows.

With this transition now in effect, development teams relying on Gemini CLI for repository management and automated tasks must establish a migration path. In this post, I will show you how to transition seamlessly by building an automated "first-pass" pull request reviewer using the Google [Antigravity SDK](https://antigravity.google/product/antigravity-sdk) and the [run-agy-sdk](https://github.com/rsamborski/run-agy-sdk) composite [GitHub Action](https://github.com/features/actions).

## The orchestration tax

The approach I am proposing also solves another pressing issue for modern engineering teams: cognitive overload. As [Addy Osmani](https://x.com/addyosmani) recently pointed out, there is an [orchestration tax](https://x.com/addyosmani/status/2059844244907696186) to using AI for coding. The time developers save generating code is often pushed onto reviewers as large, complex PRs, causing context switching and cognitive fatigue.

By offloading the tedious "first pass" search to an Antigravity agent, human reviewers can mitigate this tax and focus on high-level architecture and safeguarding quality.

## Why we need automated agentic code reviews

AI-generated code can be deceptively good. It is often clean, well-documented, and syntactically correct. This makes it harder for human reviewers to spot subtle logical bugs or security vulnerabilities that might not be immediately obvious.

In a large codebase, manually verifying every change is simply not feasible. This is why we need autonomous agents that can step into the codebase and analyze it from a fresh perspective.

But if a developer used an LLM to generate the code, how can we trust another AI to find the bugs? The answer lies in the agent architecture and context separation.

Developers might write code using any tool — whether it's CLI, an IDE extension, or various models like Gemini 3.5 Flash or Gemini 3.1 Pro. The reviewer, however, is a managed Antigravity Agent running via a separate SDK integration. This agent has a specialized, low-freedom persona and strict system instructions that force it to act as an adversarial code auditor rather than a developer. Furthermore, it operates in an isolated environment. Because it has a different system prompt, safety guardrails, and context boundaries, the agent reviews the changes with a completely fresh perspective, catching logical bugs and vulnerabilities that the original generator might miss.

To demonstrate it in practice I created an agentic review pipeline, which:

1. Leverages a managed [Antigravity Agent](https://ai.google.dev/gemini-api/docs/antigravity-agent) configured via the SDK to review the code. The agent uses advanced reasoning to explore files and verify logic under strict guidelines.  
2. Runs reviews inside isolated workspaces or sandboxes with custom policies to prevent shell or arbitrary code execution risks.  
3. Enables the agent to use the GitHub MCP server to interact directly with the environment to write pull request comments and reviews.  
4. Avoids using the `synchronize` trigger in pull request workflows to prevent redundant review runs and endless loops. Instead, runs reviews on `opened` and `reopened` events, and triggers subsequent passes manually by posting a `@agy /review` comment on the PR.

![Agentic review pipeline](artifacts/pipeline_diagram.png)

You can find the code at [run-agy-sdk](https://github.com/rsamborski/run-agy-sdk).

## What is run-agy-sdk?

The [run-agy-sdk](https://github.com/rsamborski/run-agy-sdk) is a composite GitHub Action that runs the Google Antigravity SDK (`google-antigravity`) directly on the GitHub Actions host runner.

## Why run on the host instead of a container?

By running directly on the host, the Antigravity SDK has access to the host's Docker daemon. This allows the SDK to spawn Docker-based MCP servers (like the GitHub MCP server) to read files, run tests, and post reviews.

Sub-containers should ideally run with restricted network access and read-only filesystems where possible to prevent an LLM from being tricked into executing arbitrary destructive commands. The limited set of permissions is handled in the GitHub Action configuration ([see here](https://github.com/rsamborski/run-agy-sdk/blob/da0ff77fc9dfc82e5ad89a430bc51476aeb8f867/.github/workflows/antigravity-autonomous-review.yml#L33)). Whereas the Antigravity agent has a limited number of tools it can use from GitHub MCP ([see here](https://github.com/rsamborski/run-agy-sdk/blob/da0ff77fc9dfc82e5ad89a430bc51476aeb8f867/run_agent.py#L160-L161)).

Moreover the workflow is explicitly protected from running automatically on forks, preventing unauthorized code execution. The automated review job will only run if the pull request originates from the same repository ([see here](https://github.com/rsamborski/run-agy-sdk/blob/da0ff77fc9dfc82e5ad89a430bc51476aeb8f867/.github/workflows/antigravity-autonomous-review.yml#L45)). On-demand reviews triggered by commenting `@agy /review` are restricted so that they can only be initiated by maintainers ([see here](https://github.com/rsamborski/run-agy-sdk/blob/da0ff77fc9dfc82e5ad89a430bc51476aeb8f867/.github/workflows/antigravity-autonomous-review.yml#L59-L61)).

## Demonstration walkthrough

The demo below shows the action triggered by a new PR:

![Demo screencast](artifacts/antigravity_pr_review.gif)

# Implementation: How to install the action in your repo

Let's walk through the setup process step-by-step.

## Step 1: Add your API key to GitHub secrets

The action requires a Google Gemini or Antigravity API key to authenticate language model interactions.

1. Generate your API key.  
2. Navigate to your target GitHub repository and go to **Settings** > **Secrets and variables** > **Actions**.  
3. Create a new Repository Secret named `ANTIGRAVITY_API_KEY` and paste your API key as the value.

## Step 2: Configure the GitHub Actions workflow

Add a new file in your repository at `.github/workflows/antigravity-review.yml` and add the following configuration:

```
name: '🔎 Antigravity PR Review'

on:
  pull_request:
    types: [opened, reopened]
  workflow_dispatch:

concurrency:
  group: '${{ github.workflow }}-${{ github.event.pull_request.number || github.ref_name }}'
  cancel-in-progress: true

jobs:
  antigravity-review:
    runs-on: 'ubuntu-latest'
    timeout-minutes: 20
    
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
        uses: 'rsamborski/run-agy-sdk@main'
        id: 'agy_pr_review'
        with:
          api-key: '${{ secrets.ANTIGRAVITY_API_KEY }}'
          github-token: '${{ secrets.GITHUB_TOKEN }}'
          mode: 'review'
          prompt: '/antigravity-review'
          trust-workspace: 'true'
          sandbox-profile: 'true'
```

**Pro Tip:** Pin the action version to a specific commit SHA (e.g., `rsamborski/run-agy-sdk@<commit-sha>`) rather than using `@main`. This prevents unexpected breaks from upstream updates.

While you can reference `run-agy-sdk` directly in your workflows, its real power lies in using it as a blueprint. I encourage you to [fork the repository](https://github.com/rsamborski/run-agy-sdk) and use it as a template to build your own custom, agentic GitHub Actions. By modifying the safety policies, custom tools, or prompts in `run_agent.py`, you can tailor the agent's review behavior to your team's specific codebase, style guidelines, and compliance rules.

For a full workflow template supporting both automated PR reviews and comment-triggered reviews, refer to the [workflows](https://github.com/rsamborski/run-agy-sdk/blob/main/.github/workflows) folder in the repository.

# Conclusions

Automating code reviews is a necessity as AI-generated code volumes increase. By using `run-agy-sdk`, you can run the Antigravity SDK to review PRs automatically and shift more of the burden of code quality assurance away from human reviewers.

- Access the full source code in the [GitHub Repository](https://github.com/rsamborski/run-agy-sdk).  
- Read the documentation to customize the prompts and mode.  
- Feel free to fork the repository and build your own automation.

# Acknowledgments

This project was inspired by the [run-gemini-cli](https://github.com/google-github-actions/run-gemini-cli) action, while shifting to the recently released Antigravity SDK. It is a personal sample implementation of how to run the Antigravity SDK in a GitHub Action, and is not an officially supported Google product.

# Let’s connect!

I’d love to hear how you’re using Antigravity for your agentic workflows. Are you building automated code review loops or keeping a tighter leash on your agents?

- Connect with me on [LinkedIn](https://www.linkedin.com/in/remigiusz-samborski/)  
- Follow me on [X](https://x.com/RemikSamborski)  
- Catch me on [Bluesky](https://bsky.app/profile/rsamborski.bsky.social)
