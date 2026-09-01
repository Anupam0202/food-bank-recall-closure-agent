import unittest
from io import BytesIO

from PIL import Image

from app.domain.exceptions import ValidationError
from app.security import validate_upload


class FileSecurityTests(unittest.TestCase):
    def image_bytes(self, size=(10, 10), fmt="PNG"):
        output = BytesIO()
        Image.new("RGB", size, "white").save(output, format=fmt)
        return output.getvalue()

    def test_invalid_type_rejected(self):
        with self.assertRaises(ValidationError):
            validate_upload(b"<svg/>", "image/svg+xml", "image", 100, "x.svg")

    def test_oversized_file_rejected(self):
        with self.assertRaises(ValidationError):
            validate_upload(b"x" * 11, "text/plain", "document", 10, "notice.txt")

    def test_extension_mismatch_rejected(self):
        with self.assertRaises(ValidationError):
            validate_upload(self.image_bytes(), "image/png", "image", 10000, "image.jpg")

    def test_actual_image_format_must_match(self):
        with self.assertRaises(ValidationError):
            validate_upload(self.image_bytes(fmt="JPEG"), "image/png", "image", 10000, "image.png")

    def test_dimension_limit(self):
        with self.assertRaises(ValidationError):
            validate_upload(self.image_bytes((6001, 1)), "image/png", "image", 100000, "wide.png")

    def test_valid_png(self):
        validate_upload(self.image_bytes(), "image/png", "image", 10000, "image.png")

    def test_malformed_json_rejected(self):
        with self.assertRaises(ValidationError):
            validate_upload(b"{broken", "application/json", "document", 100, "notice.json")

    def test_text_null_bytes_rejected(self):
        with self.assertRaises(ValidationError):
            validate_upload(b"recall\x00notice", "text/plain", "document", 100, "notice.txt")
