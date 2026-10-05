"""OpenRouter workflow generation with deterministic offline demo templates."""

import json
import os
import re
from dotenv import load_dotenv
from pydantic import ValidationError

from .models import Workflow

load_dotenv()

SYSTEM_PROMPT = '''Convert the user request into executable workflow JSON only. Schema: {"name": string, "description": string, "steps": [{"id": string, "type": "api|tool|transform|validation|condition|approval|error_handler", "action": string|null, "condition": string|null, "approver": string|null, "input": {}, "on_success": string|null, "on_failure": string|null}]}. Prefer sequential string IDs such as step1, step2, and step3, and use exactly the same IDs in on_success/on_failure references. Numeric IDs are also accepted. Use only actions get_order, validate_order, create_order, cancel_order, get_customer, send_email, process_refund; transformations multiply/add/copy; validations validate_order/positive/required. Connect steps using IDs, include both branches on conditions and approvals, avoid unreachable/dangling references, express conditions using amount/total comparisons or payment_status equality, never include Python/expression code, and return no markdown.
IMPORTANT WORKFLOW RULES:
- Generate ONLY the steps required by the user's requirement.
- Never invent an API, tool, approval, or other operation that the user did not request.
- A workflow may end after a successful transformation or validation step.
- Never generate an API step with a null, empty, or "None" action.
- Every API step must have a meaningful non-empty action.
- Every validation step must have a meaningful validation action.
- Every transformation step must have a meaningful transformation action.
- Terminal steps may have on_success: null.'''


def _local_workflow(requirement: str) -> Workflow:
    text = requirement.lower()
    amount_match = re.search(r"(?:above|over|greater than)\s+(\d+(?:\.\d+)?)", text)
    limit = float(amount_match.group(1)) if amount_match else 10000
    if "refund" in text:
        steps = [
            {"id": "check_amount", "type": "condition", "condition": f"amount > {limit}", "input": {"amount": limit + 1}, "on_success": "approval", "on_failure": "refund"},
            {"id": "approval", "type": "approval", "approver": "Finance manager", "on_success": "refund", "on_failure": "cancel"},
            {"id": "refund", "type": "api", "action": "process_refund", "input": {"amount": limit + 1}},
            {"id": "cancel", "type": "tool", "action": "cancel_order"},
        ]
        name = "Refund Approval"
    elif "payment" in text and ("fail" in text or "failed" in text):
        steps = [
            {"id": "validate_payment", "type": "validation", "action": "required", "input": {"field": "payment_status", "payment_status": "failed"}, "on_success": "payment_failed"},
            {"id": "payment_failed", "type": "condition", "condition": "payment_status == failed", "input": {"payment_status": "failed"}, "on_success": "notify", "on_failure": "done"},
            {"id": "notify", "type": "tool", "action": "send_email", "input": {"to": "customer@example.com", "subject": "Payment failed"}},
            {"id": "done", "type": "error_handler", "action": "handle_error"},
        ]
        name = "Payment Failure Notification"
    elif "calculat" in text or "total price" in text:
        qty = int(re.search(r"(\d+)\s+products?", text).group(1)) if re.search(r"(\d+)\s+products?", text) else 3
        price = float(re.search(r"(?:costing|at|of)\s+(\d+(?:\.\d+)?)", text).group(1)) if re.search(r"(?:costing|at|of)\s+(\d+(?:\.\d+)?)", text) else 500
        steps = [
            {"id": "calculate_total", "type": "transform", "action": "multiply", "input": {"left": qty, "right": price}, "on_success": "validate_total"},
            {"id": "validate_total", "type": "validation", "action": "positive", "input": {"value": qty * price}},
        ]
        name = "Calculate and Validate Total"
    else:
        steps = [
            {"id": "load_order", "type": "api", "action": "get_order", "input": {"amount": limit + 5000}, "on_success": "validate_order"},
            {"id": "validate_order", "type": "validation", "action": "validate_order", "on_success": "check_amount", "on_failure": "handle_error"},
            {"id": "check_amount", "type": "condition", "condition": f"amount > {limit}", "on_success": "approval", "on_failure": "create_order"},
            {"id": "approval", "type": "approval", "approver": "Manager", "on_success": "create_order", "on_failure": "cancel_order"},
            {"id": "create_order", "type": "api", "action": "create_order"},
            {"id": "cancel_order", "type": "tool", "action": "cancel_order"},
            {"id": "handle_error", "type": "error_handler", "action": "handle_error"},
        ]
        name = "Customer Order Processing"
    return Workflow.model_validate({"name": name, "description": "Generated using the local deterministic demo template.", "steps": steps})


def generate_workflow(user_requirement: str) -> Workflow:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key or os.getenv("WORKFLOW_GENERATION_MODE", "").lower() == "local":
        return _local_workflow(user_requirement)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key, base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))
        response = client.chat.completions.create(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"), temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_requirement}],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("The model returned an empty response")
        try:
            workflow_data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("The model returned malformed workflow JSON.") from exc
        try:
            return Workflow.model_validate(workflow_data)
        except ValidationError as exc:
            issues = "; ".join(
                f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}"
                for issue in exc.errors(include_input=False)
            )
            raise RuntimeError(f"The model returned an invalid workflow: {issues}") from exc
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError("Workflow generation failed. Check the LLM configuration and try again.") from exc
