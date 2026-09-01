class DomainError(Exception):
    """Base exception safe to map to a user-facing error."""


class InvalidTransition(DomainError):
    """Requested incident transition is not permitted."""


class AuthorizationError(DomainError):
    """Authentication or CSRF verification failed."""


class UnsafeActionError(DomainError):
    """An action would cross a product safety boundary."""


class ValidationError(DomainError):
    """Untrusted input failed bounded validation."""


class TransientModelError(DomainError):
    """A model call may succeed on bounded retry."""


class ModelSchemaError(DomainError):
    """Model output did not satisfy the required schema."""


class RetryableWorkflowError(DomainError):
    """Workflow failed after a durable retry checkpoint."""


class TerminalWorkflowError(DomainError):
    """Workflow cannot be retried without corrected input."""
