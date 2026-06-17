# Video Script: Taming Code Review Fatigue with run-agy-sdk

* **Target Duration:** ~2.5 minutes (300-350 spoken words)
* **Objective:** Show how the `run-agy-sdk` GitHub Action automates the "first-pass" review of a Pull Request using the Google Antigravity SDK, catching bugs and posting inline suggestions directly to GitHub.
* **Tone:** Professional, developer-focused, engaging.

---

## Storyboard & Script

| Timecode | Visual Cues | Voiceover (Audio) | Production Tips / SFX |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:20** | **Intro**<br>- Full-screen capture of a developer staring at a massive, complex Pull Request diff on GitHub (e.g., +1,500 lines of code).<br>- Zoom in on a subtle logical bug hidden in the diff. | "AI coding assistants are boosting developer velocity like never before. But this has shifted the bottleneck to code reviews. Reviewing massive, complex pull requests causes cognitive fatigue... and that is exactly when critical bugs slip into production." | *Subtle, modern electronic synth music starts, low volume.*<br><br>**Visual:** Add a red highlight circle over the hidden bug on screen. |
| **0:20 - 0:45** | **Introducing run-agy-sdk**<br>- Transition to the GitHub repository page of `rsamborski/run-agy-sdk`. Show the repository description.<br>- Switch code editor view to `.github/workflows/antigravity-review.yml`. Highlight the `pull_request` trigger and the `uses: rsamborski/run-agy-sdk@main` step. | "What you need is a hybrid approach. Meet `run-agy-sdk`. A custom GitHub Action powered by the Google Antigravity SDK that automates the first pass of your code reviews. By adding a simple YAML file to your repository, you deploy an autonomous code-auditing agent." | **Visual:** Smooth highlight scroll down the workflow file, focusing on lines 103-107 (`pull_request` triggers) and 128-130 (`uses` action). |
| **0:45 - 1:10** | **The PR Trigger**<br>- Screen capture of a terminal: run `git push origin feature-branch`. <br>- Switch to GitHub and show a Pull Request being opened: "Refactoring database connections".<br>- Click "Create pull request". | "Let's see it in action. A developer pushes a new branch and creates a pull request. Immediately, GitHub Actions registers the pull_request event and kicks off the Antigravity review workflow automatically." | **Visual:** Show the PR creation screen, then immediately transition to the 'Actions' tab showing the review workflow status starting. |
| **1:10 - 1:35** | **The Agent in Action (Behind the Scenes)**<br>- Show the step logs in the GitHub Action runner.<br>- Highlight the agent setup: installing `google-antigravity`, downloading the GitHub MCP server, and launching the agent.<br>- Display a conceptual diagram/slide showing: *Antigravity SDK -> Secure Sandbox -> GitHub MCP Server -> PR Diff*. | "Under the hood, the Antigravity SDK spins up a managed agent running in a secure, sandboxed environment. Using the GitHub MCP server, the agent securely reads the PR diff, examines the modified code, and audits it for correctness, security, and performance constraints." | **Visual:** Overlay a clean, semi-transparent schema diagram on screen showing the sandboxed execution model. |
| **1:35 - 2:15** | **The Review Results**<br>- Return to the GitHub Pull Request conversation page. Show the page reloading to reveal review comments.<br>- Zoom in on the comments: point out the colored severity dots (`🔴` Critical, `🟠` High, `🟡` Medium, `🟢` Low).<br>- Focus on a comment containing a ````suggestion```` block. Show the mouse cursor clicking the "Commit suggestion" button directly on GitHub. | "Once the audit is complete, the agent publishes its review directly on the PR. It labels findings with clear severity tags: red for critical correctness issues, green for minor style notes. Best of all, it provides ready-to-apply inline code suggestions that you can commit directly from GitHub with a single click." | *Upbeat music swell.*<br><br>**Visual:** Capture the click action of applying the suggestion. Show the commit dialog overlay confirming the fix. |
| **2:15 - 2:30** | **Conclusion & Call to Action**<br>- Show the high-level "Review Summary" comment posted at the top of the PR.<br>- Transition to the GitHub repository URL screen: `github.com/rsamborski/run-agy-sdk`. | "No more wasting time on manual syntax checks or missing hidden logic errors. Reclaim your focus for high-level architecture. Fork `run-agy-sdk` today to customize your own secure agentic workflows." | *Music fades out.*<br><br>**Visual:** Show the LinkedIn and X handle overlays for connect opportunities. |

---

## Demo PR Code Example (To use during screencast recording)

To make the demo realistic, create a PR that adds a new file containing a simple logical flaw, such as a missing error check or resource leak.

### Example file with flaw (`db_helper.py`):
```python
import sqlite3

def save_user(username, email):
    # Bug: Resource leak (connection is never closed) and possible SQL injection
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO users VALUES ('{username}', '{email}')")
    conn.commit()
    return True
```

### Agent's posted review suggestions:
* **🔴 Critical (SQL Injection):**
  ```python
  # Suggestion: Use parameterized query to prevent SQL Injection
  cursor.execute("INSERT INTO users VALUES (?, ?)", (username, email))
  ```
* **🟠 High (Resource Leak):**
  ```python
  # Suggestion: Use context manager to ensure database connections are closed
  with sqlite3.connect("users.db") as conn:
      cursor = conn.cursor()
      # ...
  ```
