"""Deterministic demo operations exposed to workflows through allowlists."""

from typing import Any, Dict


def get_order(input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    return {"order_id": "ORD-1001", "customer": "Salman", "amount": input_data.get("amount", 15000), "payment_status": input_data.get("payment_status", "paid")}


def validate_order(input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    order = input_data or context.get("order", {})
    if float(order.get("amount", 0)) <= 0:
        raise ValueError("Order amount must be greater than zero")
    return {"valid": True, "order_id": order.get("order_id"), "amount": order.get("amount")}


def create_order(input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    order = input_data or context.get("order", {})
    return {"status": "created", "order_id": order.get("order_id", "ORD-DEMO")}


def cancel_order(input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    order = input_data or context.get("order", {})
    return {"status": "cancelled", "order_id": order.get("order_id", "ORD-DEMO")}


def send_email(input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "email_sent", "to": input_data.get("to", context.get("customer_email", "customer@example.com")), "subject": input_data.get("subject", "Workflow notification")}


def get_customer(input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    return {"customer_id": input_data.get("customer_id", "CUS-1001"), "email": input_data.get("email", "customer@example.com")}


def process_refund(input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "processed", "refund_id": input_data.get("refund_id", "REF-DEMO"), "amount": input_data.get("amount", 0)}


TOOLS = {"get_order": get_order, "validate_order": validate_order, "create_order": create_order, "cancel_order": cancel_order, "send_email": send_email, "get_customer": get_customer, "process_refund": process_refund}
API_ACTIONS = {"get_order", "create_order", "cancel_order", "get_customer", "process_refund", "send_email"}
TRANSFORMS = {"multiply": "multiply", "add": "add", "copy": "copy"}


def run_transform(action: str, values: Dict[str, Any]) -> Dict[str, Any]:
    """Run a predefined deterministic transformation."""

    operation = TRANSFORMS.get(action)

    if operation == "multiply":
        # Support both {left, right} and descriptive inputs such as
        # {quantity, price}.
        if "left" in values and "right" in values:
            left = values["left"]
            right = values["right"]
        else:
            numeric_values = [
                value for value in values.values()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            ]

            if len(numeric_values) < 2:
                raise ValueError(
                    "Multiply requires at least two numeric input values"
                )

            left, right = numeric_values[0], numeric_values[1]

        return {"value": float(left) * float(right)}

    if operation == "add":
        if "left" in values and "right" in values:
            left = values["left"]
            right = values["right"]
        else:
            numeric_values = [
                value for value in values.values()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            ]

            if len(numeric_values) < 2:
                raise ValueError(
                    "Add requires at least two numeric input values"
                )

            left, right = numeric_values[0], numeric_values[1]

        return {"value": float(left) + float(right)}

    if operation == "copy":
        if "value" not in values:
            raise ValueError("Copy requires a 'value' input")
        return {"value": values["value"]}

    raise ValueError(f"Unsupported transformation: {action}")