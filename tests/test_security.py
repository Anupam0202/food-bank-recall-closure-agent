import unittest
from io import BytesIO

from pypdf import PdfWriter

from app.domain.exceptions import AuthorizationError, ValidationError
from app.security import payload_hash, require_csrf, safe_filename, validate_upload, verify_secret


class SecurityTests(unittest.TestCase):
    def test_constant_time_secret_interface(self):
        self.assertTrue(verify_secret("expected", "expected"))
        self.assertFalse(verify_secret("wrong", "expected"))

    def test_csrf_required(self):
        with self.assertRaises(AuthorizationError):
            require_csrf({"csrf_token": "abc"}, "wrong")

    def test_pdf_signature(self):
        output = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(output)
        validate_upload(output.getvalue(), "application/pdf", "document", 4096, "notice.pdf")
        with self.assertRaises(ValidationError):
            validate_upload(b"not-pdf", "application/pdf", "document", 1024)

    def test_randomized_filename_preserves_suffix(self):
        generated = safe_filename("../../unsafe.PDF")
        self.assertTrue(generated.endswith(".pdf"))
        self.assertNotIn("unsafe", generated)

    def test_payload_hash_is_stable(self):
        self.assertEqual(payload_hash(b"x"), payload_hash(b"x"))
