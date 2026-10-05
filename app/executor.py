from typing import Any, Dict, List, Optional

from .models import Workflow
from .tools import API_ACTIONS, TOOLS, run_transform
from .validator import validate_workflow


def _truthy_condition(
    expression: str,
    context: Dict[str, Any],
    step_input: Dict[str, Any],
) -> bool:
    """Evaluate a deliberately small condition vocabulary without eval()."""

    text = expression.lower().strip()

    scope = {
        **context,
        **step_input,
    }

    aliases = {
        "amount": scope.get(
            "amount",
            scope.get("order", {}).get("amount", 0),
        ),
        "total": scope.get(
            "total",
            scope.get("value", 0),
        ),
        "payment_status": scope.get(
            "payment_status",
            scope.get("order", {}).get("payment_status", ""),
        ),
        "condition_result": scope.get(
            "condition_result",
            False,
        ),
    }

    import re

    match = re.fullmatch(
        r"\s*(amount|total)\s*(>=|<=|>|<|==|!=)\s*(-?\d+(?:\.\d+)?)\s*",
        text,
    )

    if match:
        left = match.group(1)
        operator = match.group(2)
        right = float(match.group(3))

        a = float(aliases[left])

        return {
            ">": a > right,
            "<": a < right,
            ">=": a >= right,
            "<=": a <= right,
            "==": a == right,
            "!=": a != right,
        }[operator]

    match = re.fullmatch(
        r"""payment_status\s*(==|!=)\s*['"]?(failed|paid|success)['"]?""",
        text,
    )

    if match:
        equal = (
            str(aliases["payment_status"]).lower()
            == match.group(2)
        )

        return equal if match.group(1) == "==" else not equal

    if text in {"true", "always"}:
        return True

    if text in {"false", "never"}:
        return False

    raise ValueError(f"Unsupported condition: {expression}")


def _execute_step(
    step: Any,
    context: Dict[str, Any],
    approvals: Dict[str, bool],
) -> Any:

    payload = dict(step.input or {})

    # CONDITION
    if step.type == "condition":
        return {
            "condition": step.condition,
            "result": _truthy_condition(
                step.condition or "",
                context,
                payload,
            ),
        }

    # APPROVAL
    if step.type == "approval":
        decision = approvals.get(
            step.id,
            approvals.get("default"),
        )

        if decision is None:
            return {
                "approval_required": True,
                "approver": step.approver,
                "decision": "pending",
            }

        return {
            "approval_required": True,
            "approver": step.approver,
            "decision": "approved" if decision else "rejected",
        }

    # TRANSFORM
    if step.type == "transform":
        source = {
            **context,
            **payload,
        }

        return run_transform(
            step.action or "",
            source,
        )

    # VALIDATION
    if step.type == "validation":

        # Validate order
        if step.action == "validate_order":

            order = payload or context.get("order", {})

            # If the workflow didn't provide an order,
            # use deterministic demo data.
            if not order:
                order = {
                    "order_id": "ORD-1001",
                    "customer": "Salman",
                    "amount": 15000,
                    "payment_status": "failed",
                }

            if float(order.get("amount", 0)) <= 0:
                raise ValueError(
                    "Order amount must be greater than zero"
                )

            return {
                "valid": True,
                "amount": order.get("amount"),
                "payment_status": order.get(
                    "payment_status"
                ),
            }

        # Positive validation
        if step.action == "positive":

            value = payload.get(
                "value",
                context.get(
                    "value",
                    context.get("total", 0),
                ),
            )

            if float(value) <= 0:
                raise ValueError(
                    "Value must be greater than zero"
                )

            return {
                "valid": True,
                "value": value,
            }

        # Required validation
        if step.action == "required":

            field = payload.get("field")

            if not field or not payload.get(
                field,
                context.get(field),
            ):
                raise ValueError(
                    f"Required value is missing: {field}"
                )

            return {
                "valid": True,
                "field": field,
            }

        raise ValueError(
            f"Unsupported validation action: {step.action}"
        )

    # API / TOOL
    action = step.action or ""

    if step.type == "api" and action not in API_ACTIONS:
        raise ValueError(
            f"Unsupported API action: {action}"
        )

    if step.type in {"api", "tool"}:

        if action not in TOOLS:
            raise ValueError(
                f"Unsupported tool action: {action}"
            )

        result = TOOLS[action](
            payload,
            context,
        )

        if action == "get_order":
            context["order"] = result

        if action == "get_customer":
            context["customer"] = result

        return result

    # ERROR HANDLER
    if step.type == "error_handler":
        return {
            "handled": True,
            "error": context.get("last_error"),
        }

    raise ValueError(
        f"Unsupported step type: {step.type}"
    )


def execute_workflow(
    workflow: Workflow,
    approvals: Optional[Dict[str, bool]] = None,
) -> List[Dict[str, Any]]:

    check = validate_workflow(workflow)

    if not check["valid"]:
        return [
            {
                "status": "failed",
                "error": "Workflow validation failed",
                "details": check["errors"],
            }
        ]

    results: List[Dict[str, Any]] = []

    context: Dict[str, Any] = {}

    approval_choices = approvals or {}

    steps = {
        step.id: step
        for step in workflow.steps
    }

    current: Optional[str] = (
        workflow.steps[0].id
    )

    visited = set()

    while current:

        # Detect circular workflow
        if current in visited:
            results.append(
                {
                    "step_id": current,
                    "status": "failed",
                    "error": (
                        "Circular workflow transition "
                        "detected; execution stopped"
                    ),
                }
            )
            break

        visited.add(current)

        step = steps.get(current)

        # Missing step
        if step is None:
            results.append(
                {
                    "step_id": current,
                    "status": "failed",
                    "error": (
                        "Workflow references a "
                        "missing step"
                    ),
                }
            )
            break

        try:

            value = _execute_step(
                step,
                context,
                approval_choices,
            )

            status = (
                "pending"
                if (
                    step.type == "approval"
                    and value.get("decision") == "pending"
                )
                else "success"
            )

            results.append(
                {
                    "step_id": step.id,
                    "type": step.type,
                    "status": status,
                    "result": value,
                }
            )

            # CONDITION
            if step.type == "condition":

                context["condition_result"] = (
                    value["result"]
                )

                current = (
                    step.on_success
                    if value["result"]
                    else step.on_failure
                )

            # APPROVAL
            elif step.type == "approval":

                if status == "pending":
                    break

                current = (
                    step.on_success
                    if value["decision"] == "approved"
                    else step.on_failure
                )

            # ALL OTHER STEPS
            else:

                if step.type == "transform":

                    context["value"] = (
                        value["value"]
                    )

                    context["total"] = (
                        value["value"]
                    )

                current = step.on_success

        except Exception as exc:

            context["last_error"] = str(exc)

            results.append(
                {
                    "step_id": step.id,
                    "type": step.type,
                    "status": "failed",
                    "error": str(exc),
                }
            )

            if step.on_failure:
                current = step.on_failure
            else:
                break

    return results