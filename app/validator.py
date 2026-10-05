from typing import Any, Dict

from .models import Workflow
from .tools import API_ACTIONS, TOOLS, TRANSFORMS


def validate_workflow(workflow: Workflow) -> Dict[str, Any]:
    errors = []
    ids = [step.id for step in workflow.steps]
    known = set(ids)
    if not workflow.name.strip():
        errors.append("Workflow name cannot be empty")
    for step in workflow.steps:
        if not step.id.strip():
            errors.append("Step ID cannot be empty")
    if len(ids) != len(known):
        errors.extend(f"Duplicate step ID: {sid}" for sid in sorted({x for x in ids if ids.count(x) > 1}))
    for step in workflow.steps:
        if step.type in {"api", "tool", "transform", "validation"} and not step.action:
            errors.append(f"{step.id}: action is required for {step.type}")
        if step.type == "api" and step.action not in API_ACTIONS:
            errors.append(f"{step.id}: unsupported API action '{step.action}'")
        if step.type == "tool" and step.action not in TOOLS:
            errors.append(f"{step.id}: unsupported tool action '{step.action}'")
        if step.type == "transform" and step.action not in TRANSFORMS:
            errors.append(f"{step.id}: unsupported transform '{step.action}'")
        if step.type == "validation" and step.action not in {"validate_order", "positive", "required"}:
            errors.append(f"{step.id}: unsupported validation action '{step.action}'")
        if step.type == "condition" and not step.condition:
            errors.append(f"{step.id}: condition is required")
        if step.type == "approval" and not (step.approver and step.approver.strip()):
            errors.append(f"{step.id}: approver is required")
        for edge in (step.on_success, step.on_failure):
            if edge and edge not in known:
                errors.append(f"{step.id}: transition points to unknown step '{edge}'")
        if step.type == "condition" and (not step.on_success or not step.on_failure):
            errors.append(f"{step.id}: condition requires on_success and on_failure branches")
        if step.type == "approval" and (not step.on_success or not step.on_failure):
            errors.append(f"{step.id}: approval requires approved and rejected transitions")
    return {"valid": not errors, "errors": errors}
