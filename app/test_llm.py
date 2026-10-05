import unittest
from unittest.mock import patch

from app.llm import generate_workflow


class GenerationTests(unittest.TestCase):
    def test_local_generation_without_key(self):
        with patch.dict("os.environ", {"WORKFLOW_GENERATION_MODE": "local"}):
            workflow = generate_workflow("Process order and request manager approval if amount is above 10000")
        self.assertEqual(workflow.name, "Customer Order Processing")


if __name__ == "__main__":
    unittest.main()
