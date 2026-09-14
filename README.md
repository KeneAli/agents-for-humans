# SCÉANCE

### Always watching. Ready to recover.

SCÉANCE is an agentic logistics recovery system that monitors shipment disruptions, investigates their operational and business impact, evaluates recovery options, and executes an approved recovery action.

It is designed for **logistics operations teams, control towers, and supply chain planners** who need to respond quickly to disruptions without giving up human control over consequential decisions.

---

## How it works

When a disruption occurs, SCÉANCE:

1. Investigates the shipment and operational context
2. Assesses the business consequences of the disruption
3. Evaluates available recovery options using deterministic business logic
4. Prepares a recovery recommendation
5. Requests human approval before a consequential action
6. Executes the approved recovery
7. Verifies the resulting operational state

If no recovery is necessary, the agent records the investigation and ends the run without requesting unnecessary intervention.

```text
Disruption
    ↓
Agent investigation
    ↓
Business impact assessment
    ↓
Recovery evaluation
    ↓
Recommendation
    ↓
Human approval
   ↙       ↘
Reject    Approve
  ↓          ↓
Stop      Execute
             ↓
          Verify
             ↓
          Resolved
```

---

## What makes SCÉANCE agentic?

The LLM is responsible for **investigation and orchestration** through a set of operational tools.

Consequential recovery decisions are controlled by deterministic business logic rather than relying on the LLM to invent or directly determine operational actions.

Human approval remains the final authorization step before recovery execution.

---

## Key features

- **Agentic investigation** using Strands Agents and Amazon Bedrock
- **Deterministic recovery evaluation** based on operational and business constraints
- **Human-in-the-loop approval** for consequential recovery actions
- **Persistent run state and audit events** using Amazon DynamoDB
- **Recovery execution and verification**
- **Operational activity trace** showing what the agent actually did during a recovery run

---

## Technology

### Backend

- Python 3.14
- Strands Agents
- Amazon Bedrock
- Amazon Bedrock AgentCore
- AWS Lambda
- Amazon EventBridge
- Amazon DynamoDB
- Boto3
- Pandas / PyArrow / NumPy
- Pytest

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- React Router
- TanStack Query
- Lucide React

---

## Repository structure

```text
agents-for-humans/
├── src/
│   ├── agent/          # Recovery agent and agent tools
│   ├── business/       # Recovery and consequence logic
│   ├── simulation/     # Operational state and disruption simulation
│   ├── state/          # State persistence and repositories
│   └── data_generation/
│
├── tests/               # Backend and state-management tests
├── data/                # Generated logistics datasets
├── ui/                  # React/Vite frontend
├── docs/                # Project documentation
├── pyproject.toml
├── uv.lock
└── .env.example
```

---

## Running the project locally

### Backend

Requirements:

- Python 3.14
- [uv](https://docs.astral.sh/uv/)

Install dependencies:

```bash
uv sync
```

Run the tests:

```bash
uv run pytest
```

The backend uses the following environment variables:

```env
STATE_REPOSITORY=dynamodb
DYNAMODB_TABLE_NAME=agents-for-humans-state
AWS_REGION=us-east-1
```

See `.env.example` for the available configuration.

A configured AWS environment with access to the required resources is needed to run the live AgentCore/DynamoDB workflow.

### Frontend

Requirements:

- Node.js
- npm

```bash
cd ui
npm ci
npm run dev
```

The frontend expects the backend control-plane URL through:

```env
VITE_API_BASE_URL=YOUR_API_URL
```

For a production build:

```bash
npm run build
```

For linting:

```bash
npm run lint
```

---

## Live demo

**SCÉANCE is available as a public web application.**

**Live demo:** [https://sceance.vercel.app/](https://sceance.vercel.app/)

The demo allows you to simulate a logistics disruption and follow the recovery process from investigation through human approval, execution, and verification.

No AWS credentials are required to use the demo.

---

## Architecture

The detailed architecture diagram is provided separately in the project documentation.

---

## License

This project is licensed under the **MIT License**. See [`LICENSE`](LICENSE).
