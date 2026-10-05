# Natural Language Workflow Generator
A GenAI-powered workflow generation system that converts natural-language business requirements into structured, validated, and executable workflows.
The system does not simply generate a text response. It converts a business requirement into a typed workflow containing actions, validations, conditions, API/tool operations, data transformations, human approval steps, and error-handling paths.
## 🔗 Project Links
- **Live Demo🚀:** [https://natural-language-workflow-generator.onrender.com]
---
## 📌 Problem Statement
Business requirements are often written in natural language and may contain multiple operations, validations, decisions, API calls, and approval steps.
For example:
> "Process a customer order. If the order amount is above 10000, ask the manager for approval. If approved, create the order. If rejected, cancel it."
A simple text-generation system would only describe these steps.
This project converts the requirement into a machine-readable workflow that can be:
1. Generated
2. Validated
3. Executed
4. Paused for human approval when required
5. Routed based on conditions
6. Handled safely when errors occur
---
## 🚀 Solution
The application follows this workflow:
```text
Natural Language Requirement
            ↓
      Workflow Generator
            ↓
      Structured Workflow
        (Pydantic Schema)
            ↓
    Workflow Validation
            ↓
      Graph Validation
            ↓
       Workflow Executor
            ↓
 ┌──────────┼───────────┐
 ↓          ↓           ↓
API       Condition   Approval
Tool      / Branch    / Reject
 ↓          ↓           ↓
 └──────────┴───────────┘
            ↓
       Execution Result

The generated workflow is validated before execution, preventing unsupported actions, invalid transitions, duplicate step IDs, and malformed workflow structures from being executed.

⸻

✨ Key Features

1. Natural Language → Workflow

Users can describe a business requirement in plain English.

Example:

If a customer's payment fails, validate the payment and send an email notification to the customer.

The system converts the requirement into structured workflow steps instead of returning only natural-language text.

⸻

2. Structured Workflow Schema

Workflows are represented using typed Pydantic models.

Supported step types include:

* API
* Tool
* Transform
* Validation
* Condition
* Human Approval
* Error Handler

⸻

3. Workflow Validation

Before execution, the workflow is validated for:

* Required fields
* Unique step IDs
* Supported actions
* Valid transition targets
* Valid conditions
* Valid approval branches
* Invalid workflow structures

Invalid workflows are rejected before execution.

⸻

4. Conditional Logic

Workflows can make decisions based on values such as:

* amount
* total
* payment_status

Example:

If amount > 10000
    → Request manager approval
Else
    → Continue processing

The executor follows the appropriate transition based on the condition result.

⸻

5. Human Approval

The system supports human-in-the-loop workflows.

When an approval step is reached:

Workflow
   ↓
Approval Required
   ↓
 ┌───────────┐
 ↓           ↓
Approve     Reject
 ↓           ↓
Continue    Rejection Path

The workflow pauses with a pending state until an approval decision is provided.

The browser UI provides Approve and Reject controls.

⸻

6. Data Transformation

The workflow supports controlled, named transformations instead of executing arbitrary expressions or Python code.

Example:

multiply
left = 3
right = 500
Result:
1500

Supported transformations include:

* multiply
* add
* copy

⸻

7. Error Handling

Each workflow step can define success and failure transitions.

Step
 ├── on_success → Next Step
 └── on_failure → Error Handler

If a step fails and an on_failure transition exists, execution is routed to the configured failure path.

⸻

8. Safe Execution

Generated workflow content is never evaluated as arbitrary Python code.

The executor only allows predefined actions and named transformations from an explicit allowlist.

This keeps workflow execution controlled and predictable.

⸻

🧠 GenAI Integration

The project supports OpenRouter using an OpenAI-compatible API interface.

When an API key is configured, the application can use an LLM to generate structured workflows from natural-language requirements.

For assessment/demo purposes, the application also includes deterministic local workflow templates.

This allows the application to demonstrate core workflow functionality without requiring an external API connection.

Generation Modes

LLM Mode

Uses OpenRouter for workflow generation.

User Requirement
      ↓
OpenRouter LLM
      ↓
Structured Workflow
      ↓
Validation
      ↓
Execution

Local Demo Mode

Uses deterministic templates for supported assessment scenarios.

This makes the project reproducible and allows the workflow engine to be tested without an API key.

⸻

🏗️ Architecture

                         User
                          │
                          ▼
                 FastAPI / Web UI
                          │
                          ▼
              Natural Language Input
                          │
                          ▼
                 Workflow Generator
                    ┌─────┴─────┐
                    │           │
               OpenRouter    Local Mode
                    │           │
                    └─────┬─────┘
                          ▼
                  Pydantic Workflow
                          │
                          ▼
                  Workflow Validator
                          │
                    Valid Workflow
                          │
                          ▼
                   Graph Executor
              ┌───────────┼───────────┐
              │           │           │
             API        Condition   Approval
             Tool       Transform   / Reject
              │           │           │
              └───────────┼───────────┘
                          ▼
                  Execution Results

⸻

🛠️ Technology Stack

* Python 3.10+
* FastAPI
* Pydantic v2
* OpenRouter
* OpenAI-compatible Python SDK
* HTML / CSS / JavaScript
* Git & GitHub
* Render

⸻

📁 Project Structure

natural-language-workflow-generator/
│
├── app/
│   ├── executor.py
│   ├── llm.py
│   ├── main.py
│   ├── models.py
│   ├── tools.py
│   ├── validator.py
│   ├── test_workflow.py
│   └── test_llm.py
│
├── .env
├── .gitignore
├── README.md
└── requirements.txt

Core Components

File	Responsibility
main.py	FastAPI routes and browser UI
llm.py	LLM integration and local workflow generation
models.py	Workflow and step schemas
validator.py	Workflow and graph validation
executor.py	Workflow execution engine
tools.py	Allowlisted demo tools and transformations
test_workflow.py	Workflow validation and execution tests
test_llm.py	Local generation tests

⸻

🔄 Workflow Execution

Execution starts from the first workflow step and follows the configured transition graph.

Each step can produce a result such as:

SUCCESS
FAILED
PENDING

Example:

Step 1: Validate Payment
        ↓ SUCCESS
Step 2: Send Email
        ↓ SUCCESS
Workflow Completed

For approval workflows:

Step 1: Validate Order
        ↓
Step 2: Check Amount
        ↓
Step 3: Manager Approval
       / \
      /   \
Approve   Reject
   ↓        ↓
Create    Cancel
Order     Order

The executor also tracks visited steps to prevent infinite execution loops.

⸻

🧪 Example

Input

Process a customer order. If the order amount is above 10000,
ask the manager for approval. If approved, create the order.
If rejected, cancel it.

Generated Workflow

Validate Order
      ↓
Check Amount
      ↓
Manager Approval
    /       \
Approve     Reject
  ↓           ↓
Create       Cancel
Order        Order

The workflow is validated before execution.

If approval is required, execution pauses and returns a pending state until the user selects Approve or Reject.

⸻

💳 Payment Failure Example

Requirement

If a customer's payment fails, validate the payment
and send an email notification to the customer.

Execution

Validate Payment
       ↓
Payment Failed
       ↓
Send Email
       ↓
Workflow Completed

The validation step can produce a result such as:

{
  "valid": true,
  "amount": 15000,
  "payment_status": "failed"
}

The email operation then produces a controlled demo result.

⸻

🌐 API Endpoints

GET /

Returns the browser-based workflow generator interface.

GET /health

Health check endpoint.

Example response:

{
  "status": "ok"
}

POST /generate

Generates, validates, and starts executing a workflow from a natural-language requirement.

Example request:

{
  "requirement": "If a customer's payment fails, validate the payment and send an email notification."
}

POST /execute

Continues execution of a validated workflow with optional human approval decisions.

Example:

{
  "workflow": {},
  "approvals": {
    "approval": true
  }
}

⸻

🔐 Environment Configuration

OpenRouter is optional.

Create a local .env file:

OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

Never commit API keys or other secrets to GitHub.

To force deterministic local generation:

WORKFLOW_GENERATION_MODE=local

⸻

💻 Local Setup

1. Clone the repository

git clone [GitHub Repository URL]
cd natural-language-workflow-generator

2. Create a virtual environment

Windows:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

3. Install dependencies

python -m pip install -r requirements.txt

4. Configure environment variables

Create a .env file if OpenRouter access is required.

5. Start the application

uvicorn app.main:app --reload

Open:

http://127.0.0.1:8000

⸻

🧪 Testing

Run the test suite from the project root:

python -m unittest discover -s app -p "test_*.py" -v

The tests cover workflow generation, validation, execution, conditions, transitions, and supported workflow behavior.

⸻

☁️ Deployment

The application is deployed as a web service using Render.

Production deployment runs the FastAPI application using Uvicorn:

uvicorn app.main:app --host 0.0.0.0 --port $PORT

The deployed application can be accessed through the Live Demo link at the top of this README.

⸻

⚠️ Limitations

This project is designed as a technical assessment/demo and intentionally uses controlled operations.

Current limitations:

* Demo tools do not connect to real business systems.
* Local generation supports predefined assessment scenarios.
* Arbitrary requirements require a configured LLM provider.
* Approval decisions are in-memory demo inputs.
* There is no persistent workflow-run database.
* There is no authenticated approver identity.
* The supported condition language is intentionally limited.
* The tool and transformation registry is intentionally allowlisted.

⸻

🔮 Future Improvements

For production usage, the system could be extended with:

* Persistent workflow execution state
* PostgreSQL or another production database
* Authenticated users and approvers
* Approval audit logs
* Retry policies and timeouts
* More advanced condition expressions
* Additional API/tool integrations
* Webhook triggers
* Scheduled workflows
* Workflow versioning
* Observability and execution monitoring
* Role-based access control
* Production-grade LLM structured-output validation

⸻

🎯 Assessment Objective

This project demonstrates how a GenAI system can transform natural-language business requirements into executable workflows while maintaining:

* Structured output
* Workflow validation
* Conditional execution
* Human-in-the-loop approval
* Controlled tool execution
* Error handling
* Safe transformations
* API-based execution
* Reproducible demo behavior

The key objective is to bridge the gap between natural-language business requirements and executable workflow logic.

⸻

👨‍💻 Author

Salman Paris

B.Sc. Artificial Intelligence & Machine Learning


⸻

📄 License

This project was developed as part of a technical assessment.