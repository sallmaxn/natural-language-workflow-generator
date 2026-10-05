import unittest
from unittest.mock import patch

from app.executor import execute_workflow
from app.llm import generate_workflow
from app.models import Workflow
from app.validator import validate_workflow


def order_workflow():
    return Workflow(name="Order", steps=[
        {"id": "load", "type": "api", "action": "get_order", "input": {"amount": 15000}, "on_success": "check"},
        {"id": "check", "type": "condition", "condition": "amount > 10000", "on_success": "approve", "on_failure": "cancel"},
        {"id": "approve", "type": "approval", "approver": "Manager", "on_success": "create", "on_failure": "cancel"},
        {"id": "create", "type": "api", "action": "create_order"},
        {"id": "cancel", "type": "tool", "action": "cancel_order"},
    ])


class WorkflowTests(unittest.TestCase):
    def test_valid_workflow(self):
        self.assertTrue(validate_workflow(order_workflow())["valid"])

    def test_duplicate_ids_and_invalid_reference(self):
        workflow = Workflow(name="Bad", steps=[{"id": "step", "type": "tool", "action": "send_email", "on_success": "missing"}, {"id": "step", "type": "tool", "action": "send_email"}])
        errors = validate_workflow(workflow)["errors"]
        self.assertTrue(any("Duplicate" in e for e in errors))
        self.assertTrue(any("unknown step" in e for e in errors))

    def test_reject_unsupported_action(self):
        workflow = Workflow(name="Bad", steps=[{"id": "x", "type": "tool", "action": "run_python"}])
        self.assertFalse(validate_workflow(workflow)["valid"])

    def test_condition_and_approval_branching(self):
        workflow = order_workflow()
        pending = execute_workflow(workflow)
        self.assertEqual([r["step_id"] for r in pending], ["load", "check", "approve"])
        self.assertEqual(pending[-1]["status"], "pending")
        approved = execute_workflow(workflow, {"approve": True})
        rejected = execute_workflow(workflow, {"approve": False})
        self.assertEqual(approved[-1]["step_id"], "create")
        self.assertNotIn("cancel", [r["step_id"] for r in approved])
        self.assertEqual(rejected[-1]["step_id"], "cancel")
        self.assertNotIn("create", [r["step_id"] for r in rejected])

    def test_failure_routes_to_handler(self):
        workflow = Workflow(name="Failure", steps=[
            {"id": "check", "type": "validation", "action": "positive", "input": {"value": -1}, "on_failure": "handle"},
            {"id": "handle", "type": "error_handler", "action": "handle_error"},
        ])
        results = execute_workflow(workflow)
        self.assertEqual([x["status"] for x in results], ["failed", "success"])
        self.assertEqual(results[-1]["result"]["error"], "Value must be greater than zero")

    def test_transform(self):
        workflow = Workflow(name="Total", steps=[
            {"id": "multiply", "type": "transform", "action": "multiply", "input": {"left": 3, "right": 500}, "on_success": "check"},
            {"id": "check", "type": "validation", "action": "positive"},
        ])
        results = execute_workflow(workflow)
        self.assertEqual(results[0]["result"]["value"], 1500)
        self.assertEqual(results[-1]["status"], "success")

    def test_offline_demo_generation(self):
        with patch.dict("os.environ", {"WORKFLOW_GENERATION_MODE": "local"}):
            workflow = generate_workflow("Calculate the total price for 3 products costing 500 each and validate total above zero")
        self.assertTrue(validate_workflow(workflow)["valid"])
        self.assertEqual(execute_workflow(workflow)[0]["result"]["value"], 1500)


if __name__ == "__main__":
    unittest.main()
