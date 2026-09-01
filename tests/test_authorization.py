import unittest

from app.domain.exceptions import AuthorizationError
from app.security import require_admin, require_csrf


class AuthorizationTests(unittest.TestCase):
    def test_guest_cannot_mutate(self):
        with self.assertRaises(AuthorizationError):
            require_admin({})

    def test_admin_with_csrf_can_mutate(self):
        session = {"is_admin": True, "csrf_token": "token"}
        require_admin(session)
        require_csrf(session, "token")
