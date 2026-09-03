# Agents for Humans — Development Setup & Learning Notes

## 1. Objective

This document records the development environment, AWS configuration, authentication flow, and Strands Agents setup for the **Agents for Humans Hackathon**.

The purpose is not only to build the hackathon project, but also to understand the underlying technologies and architecture well enough to explain and reproduce the system independently.

---

# 2. Local Development Environment

### Operating System

- Windows 11
- Windows PowerShell

### Development Environment

- Visual Studio Code
- Python 3.14.6
- Python virtual environment: `.venv`
- Strands Agents SDK
- AWS CLI v2.36.28

The project is being developed locally in:

`agents-for-humans/`

The Python virtual environment is used to isolate the project's Python dependencies from the rest of the system.

---

# 3. AWS Account Structure

A dedicated IAM user was created specifically for the hackathon rather than using the AWS root user.

### IAM User

`kene-hackathon`

### AWS Account

`750521684059`

### IAM Group

A dedicated hackathon group was created and permissions are attached at the group level. The `kene-hackathon` user inherits the group's permissions.

### MFA

MFA was enabled for the IAM user using an authenticator application.

This provides an additional authentication factor beyond the IAM username and password.

---

# 4. Why We Created a Dedicated IAM User

The root AWS account should not be used for normal development activities.

A dedicated IAM identity provides:

- Separation between account administration and application development
- More controlled permissions
- Easier credential management
- Reduced risk of accidentally exposing root credentials
- The ability to revoke or modify hackathon-specific access independently

The project is therefore being developed using:

`kene-hackathon`

rather than the root account.

---

# 5. AWS CLI Installation

AWS CLI v2 was installed on Windows using the official PowerShell installation method.

Installed version:

`aws-cli/2.36.28`

The AWS CLI executable was installed under the user's local AWS CLI directory.

Initially, VS Code could not find the `aws` command because VS Code had been opened before the AWS CLI installation and therefore had an outdated PATH environment.

Restarting VS Code refreshed the PATH and resolved the issue.

---

# 6. AWS CLI Authentication

The AWS CLI was configured to use the dedicated IAM user through the modern `aws login` authentication flow.

The login process required:

1. AWS account ID
2. IAM username
3. IAM password
4. MFA authentication

The AWS CLI was configured with the profile:

`kene-hackathon`

The development terminal uses:

```powershell
$env:AWS_PROFILE="kene-hackathon"
```

This tells AWS CLI-compatible applications launched from that terminal to use the `kene-hackathon` profile.

---

# 7. Authentication Verification

Authentication was successfully verified using:

```powershell
aws sts get-caller-identity
```

The response confirmed:

```text
Account: 750521684059

Arn:
arn:aws:iam::750521684059:user/kene-hackathon
```

This confirms that the local development environment is authenticated as the dedicated hackathon IAM user.

---

# 8. AWS Region

The development region was initially configured as:

`us-east-1`

AWS region:

**US East (N. Virginia)**

This region was selected because of its broad availability of AWS services and foundation models relevant to the project.

The region can be changed later if the final architecture requires services or models available elsewhere.

---

# 9. Amazon Bedrock

Amazon Bedrock will provide access to the foundation model used by the Strands agent.

The AWS CLI was successfully able to query the available foundation models:

```powershell
aws bedrock list-foundation-models --region us-east-1 --profile kene-hackathon
```

This confirmed that Anthropic Claude models are available to the account.

Available Claude Sonnet models included:

- Claude Sonnet 4 — Legacy
- Claude Sonnet 4.5 — Active
- Claude Sonnet 4.6 — Active
- Claude Sonnet 5 — Active

---

# 10. Bedrock Inference Profiles

The account was also checked for available Bedrock inference profiles.

Active profiles include:

```text
us.anthropic.claude-sonnet-4-6
us.anthropic.claude-sonnet-4-5-20250929-v1:0
us.anthropic.claude-sonnet-5
global.anthropic.claude-sonnet-4-6
global.anthropic.claude-sonnet-4-5-20250929-v1:0
global.anthropic.claude-sonnet-5
```

For initial development, **Claude Sonnet 4.6** was selected.

Selected inference profile:

```text
us.anthropic.claude-sonnet-4-6
```

---

# 11. Strands Agents SDK

The Strands Agents SDK was installed inside the project's Python virtual environment.

Strands is the agent framework that will orchestrate:

- The foundation model
- Agent reasoning
- Tools
- Tool execution
- Agent workflows
- Potential multi-agent patterns

The eventual architecture is expected to look roughly like:

```text
User
  ↓
Application
  ↓
Strands Agent
  ↓
Claude via Amazon Bedrock
  ↓
Tools / APIs / AWS Services
  ↓
Real-world action
```

The important distinction is that the hackathon requires the project to be an **agent that performs real work**, rather than simply a chatbot that answers questions.

---

# 12. MCP

The Strands MCP server was investigated but has **not been installed**.

MCP is optional for this project.

The Strands MCP server is primarily a development aid that can provide AI coding assistants with access to:

- Strands documentation
- Development prompts
- Best practices
- Debugging assistance
- Agent design patterns

It is not required for the Strands agent itself.

Therefore, MCP is currently being deliberately left out of the project until there is a clear reason to introduce it.

---

# 13. Initial Strands Test

A minimal `agent.py` was created to test the complete connection between the local development environment and Amazon Bedrock.

Conceptually:

```python
from strands import Agent

agent = Agent(
    model="us.anthropic.claude-sonnet-4-6"
)

response = agent(
    "Say hello and confirm that you are running through Amazon Bedrock."
)

print(response)
```

The test was executed from the VS Code terminal using the project's `.venv`.

---

# 14. Current Result

The test reached Amazon Bedrock successfully but was rejected at the model invocation stage.

The error was:

```text
AccessDeniedException

Your account is currently being verified.
Verification normally takes less than 2 hours.
```

The error also identified:

```text
Bedrock region: us-east-1
Model id: us.anthropic.claude-sonnet-4-6
```

This is important because it demonstrates that the following parts of the system are already functioning:

```text
VS Code
   ↓
Python
   ↓
Strands Agents SDK
   ↓
AWS authentication
   ↓
IAM user
   ↓
Amazon Bedrock
   ↓
Claude Sonnet 4.6
   ↓
Account verification block
```

Therefore, the current problem is **AWS account verification**, not a local Python, Strands, authentication, or model-selection error.

---

# 15. Current Status

| Component | Status |
|---|---|
| Windows development environment | ✅ |
| VS Code | ✅ |
| Python 3.14.6 | ✅ |
| Python virtual environment | ✅ |
| Strands Agents SDK | ✅ |
| AWS CLI v2.36.28 | ✅ |
| Dedicated IAM user | ✅ |
| IAM group | ✅ |
| MFA | ✅ |
| AWS CLI authentication | ✅ |
| AWS identity verification | ✅ |
| Bedrock access | ✅ |
| Claude Sonnet 4.6 availability | ✅ |
| Strands → Bedrock connection | ✅ Reached Bedrock |
| Bedrock model invocation | ⏳ AWS account verification |
| MCP | Not currently required |
| AgentCore | Not yet implemented |
| Hackathon agent | Not yet implemented |

---

# 16. Key Learning Points

### AWS authentication is separate from Python

The Python virtual environment does not authenticate with AWS itself.

Instead:

```text
Python / Strands
       ↓
AWS SDK / Botocore
       ↓
AWS credential provider chain
       ↓
AWS identity
```

The AWS CLI is one way of configuring and verifying this authentication.

---

### IAM controls what the application can do

Authentication answers:

> Who am I?

IAM permissions answer:

> What am I allowed to do?

Our `kene-hackathon` identity is therefore separate from the AWS root account and has its own permissions.

---

### Strands does not provide the foundation model

Strands is the **agent framework**.

Amazon Bedrock provides access to the **foundation model**.

In this project:

```text
Strands
=
Agent orchestration

Bedrock
=
Model access

Claude Sonnet
=
Foundation model
```

---

### An agent is more than an LLM call

The eventual hackathon project needs to demonstrate:

```text
Reason
  ↓
Decide
  ↓
Use a tool
  ↓
Observe result
  ↓
Reason again
  ↓
Take action
  ↓
Surface decision/result to user
```

This is one of the major distinctions between a simple LLM application and an actual agent.

---

# 17. Next Technical Milestone

Once AWS account verification is complete:

1. Re-run the minimal Strands agent.
2. Confirm successful Claude response.
3. Add a simple custom tool.
4. Test the agent's ability to reason about when to use the tool.
5. Begin developing the actual hackathon agent.
6. Introduce AWS services according to the final architecture.
7. Evaluate Amazon Bedrock AgentCore for deployment.
8. Build the end-to-end product and demo.

The goal is to understand every layer rather than simply assemble a working application.