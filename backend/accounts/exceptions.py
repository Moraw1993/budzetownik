class SetupClosedError(Exception):
    """The initial account has already been created."""


class LoginRateLimitError(Exception):
    """The allowed number of authentication attempts has been exhausted."""
