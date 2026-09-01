import unittest

from pydantic import ValidationError

from app.agents.output_schemas import PackageAssessmentSchema, RecallExtraction


class ExtractionValidationTests(unittest.TestCase):
    def test_required_product_description(self):
        with self.assertRaises(ValidationError):
            RecallExtraction(recall_number="R", product_description="", reason="Reason")

    def test_confidence_is_enum_limited(self):
        with self.assertRaises(ValidationError):
            RecallExtraction(recall_number="R", product_description="P", reason="R", confidence_category="CERTAIN")

    def test_package_assessment_forces_review(self):
        with self.assertRaises(ValidationError):
            PackageAssessmentSchema(summary="Looks similar", requires_human_review=False)
