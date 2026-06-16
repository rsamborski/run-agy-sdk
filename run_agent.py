# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import os
import re
import sys

# Attempt to import Antigravity SDK
try:
    from google.antigravity import Agent, LocalAgentConfig, types
    from google.antigravity.hooks import policy
except ImportError:
    print(
        "::error::Google Antigravity SDK is not installed. Please run 'pip install google-antigravity' first."
    )
    sys.exit(1)


# Robust TOML Parser with fallback
try:
    import tomllib

    def load_toml(f) -> dict:
        return tomllib.load(f)
except ImportError:
    try:
        import tomli

        def load_toml(f) -> dict:
            return tomli.load(f)
    except ImportError:
        # Fall back to a simple regex parser if neither is available
        class SimpleTomlParser:
            @staticmethod
            def load(f) -> dict:
                content = f.read().decode("utf-8")
                data = {}
                # Match triple-quoted prompt = """..."""
                prompt_match = re.search(
                    r'prompt\s*=\s*"""(.*?)"""', content, re.DOTALL
                )
                if prompt_match:
                    data["prompt"] = prompt_match.group(1).strip()
                # Match single/double-quoted description
                desc_match = re.search(r'description\s*=\s*["\'](.*?)["\']', content)
                if desc_match:
                    data["description"] = desc_match.group(1).strip()
                return data

        def load_toml(f) -> dict:
            return SimpleTomlParser.load(f)


async def main() -> None:
    # 1. Retrieve environment variables
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTIGRAVITY_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get(
        "GITHUB_PERSONAL_ACCESS_TOKEN"
    )
    pr_number = os.environ.get("PULL_REQUEST_NUMBER") or os.environ.get(
        "GITHUB_PR_NUMBER"
    )
    repository = os.environ.get("REPOSITORY") or os.environ.get("GITHUB_REPOSITORY")
    additional_context = os.environ.get("ADDITIONAL_CONTEXT", "")
    prompt_text = os.environ.get("PROMPT", "").strip()
    trust_workspace = os.environ.get("TRUST_WORKSPACE") == "true"

    if not api_key:
        print(
            "::error::API key is missing. Please set the ANTIGRAVITY_API_KEY or GEMINI_API_KEY env var."
        )
        sys.exit(1)

    if not github_token:
        print(
            "::error::GitHub token is missing. Please set the GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN env var."
        )
        sys.exit(1)

    # Export GITHUB_PERSONAL_ACCESS_TOKEN to ensure the child MCP process inherits it
    os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_token

    # 2. TOML Command Parsing & Variable Interpolation
    system_instructions = "You are a helpful software engineering assistant."
    chat_prompt = prompt_text

    if prompt_text.startswith("/"):
        command_name = prompt_text[1:]
        # Prevent directory traversal attacks
        if ".." in command_name or "/" in command_name or "\\" in command_name:
            print(
                f"::error::Invalid custom command name contains path separators: {command_name}"
            )
            sys.exit(1)

        action_path = os.environ.get("GITHUB_ACTION_PATH") or ""
        command_file = os.path.join(
            action_path, ".github", "commands", f"{command_name}.toml"
        )

        if os.path.exists(command_file):
            print(f"Loading custom command config from {command_file}...")
            with open(command_file, "rb") as f:
                command_data = load_toml(f)

            raw_prompt = command_data.get("prompt", "")

            # Substitute variables dynamically from the environment
            env_context = dict(os.environ)
            env_context.setdefault("REPOSITORY", repository or "")
            env_context.setdefault("PULL_REQUEST_NUMBER", pr_number or "")
            env_context.setdefault(
                "ISSUE_NUMBER", os.environ.get("GITHUB_ISSUE_NUMBER", "")
            )
            env_context.setdefault("ADDITIONAL_CONTEXT", additional_context or "")

            def replace_env_var(match: re.Match) -> str:
                var_name = match.group(1)
                # Return the value from env or a fallback empty string
                return env_context.get(var_name, "")

            interpolated_prompt = re.sub(
                r"!\{\s*echo\s+\$([A-Za-z0-9_]+)\s*\}", replace_env_var, raw_prompt
            )

            system_instructions = interpolated_prompt

            # Since system_instructions has all details, prompt chat to run the review
            chat_prompt = f"Run the command: {prompt_text}"
        else:
            print(
                f"Warning: Custom command configuration file {command_file} not found. Running with default context."
            )

    # 3. MCP Server Configuration
    # We configure the GitHub stdio MCP server for GitHub operations
    github_mcp = types.McpStdioServer(
        name="github",
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server:v0.27.0",
        ],
        enabled_tools=[
            "add_comment_to_pending_review",
            "pull_request_read",
            "pull_request_review_write",
            "add_issue_comment",
            "issue_read",
            "list_issues",
            "search_issues",
            "list_pull_requests",
            "search_pull_requests",
            "get_commit",
            "get_file_contents",
            "list_commits",
            "search_code",
        ],
    )

    # 4. Declarative Safety Policies
    if prompt_text.startswith("/"):
        # For reviews or automated tasks, deny shell/arbitrary code execution completely
        # and only allow safe MCP/GitHub tools and file views.
        policies = [
            policy.deny_all(),
            policy.allow(github_mcp),
            policy.allow("view_file"),
            policy.allow("find_file"),
        ]
    else:
        # For general goals, respect trust_workspace setting
        if trust_workspace:
            policies = [policy.allow_all()]
        else:
            policies = policy.confirm_run_command()

    # 5. Initialize and run Agent
    config = LocalAgentConfig(
        api_key=api_key,
        system_instructions=system_instructions,
        mcp_servers=[github_mcp],
        policies=policies,
        workspaces=[os.getcwd()],
    )

    print("Starting Antigravity Agent...")
    async with Agent(config) as agent:
        response = await agent.chat(chat_prompt)

        print("\n::: Agent Session Execution :::")
        full_response_text = []
        async for token in response:
            sys.stdout.write(token)
            sys.stdout.flush()
            full_response_text.append(token)
        print("\n::: End of Agent Session Execution :::")

        # Write to GITHUB_OUTPUT file if available to satisfy composite action output contract
        github_output_path = os.environ.get("GITHUB_OUTPUT")
        if github_output_path:
            full_text = "".join(full_response_text)
            try:
                import uuid

                delimiter = f"EOF_{uuid.uuid4().hex}"
                with open(github_output_path, "a", encoding="utf-8") as f:
                    # Multi-line syntax for GITHUB_OUTPUT
                    f.write(f"response<<{delimiter}\n{full_text}\n{delimiter}\n")
                    f.write("stats={}\n")  # placeholder for execution statistics
            except Exception as e:
                print(
                    f"Warning: Failed to write to GITHUB_OUTPUT: {e}", file=sys.stderr
                )


if __name__ == "__main__":
    asyncio.run(main())
