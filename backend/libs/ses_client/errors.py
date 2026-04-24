from __future__ import annotations

from libs.core.errors import ExternalServiceError


class SesError(ExternalServiceError):
    code = "ses_error"
    default_message = "AWS SES request failed"


class SesConfigurationError(SesError):
    code = "ses_configuration_error"
    default_message = "SES client is not configured"


class SesTerminalError(SesError):
    code = "ses_terminal_error"
    default_message = "SES rejected the request"


class SesTransientError(SesError):
    code = "ses_transient_error"
    default_message = "Transient SES error"


class SesThrottlingError(SesTransientError):
    code = "ses_throttling"
    default_message = "SES throttled the request"


class SesMessageRejectedError(SesTerminalError):
    code = "ses_message_rejected"
    default_message = "SES rejected the message"


class SesAuthError(SesTerminalError):
    code = "ses_auth_error"
    default_message = "SES authentication failed"


_TERMINAL_CODE_MAP: dict[str, type[SesTerminalError]] = {
    "MessageRejected": SesMessageRejectedError,
    "MailFromDomainNotVerifiedException": SesMessageRejectedError,
    "ConfigurationSetDoesNotExistException": SesTerminalError,
    "NotFoundException": SesTerminalError,
    "AccountSuspendedException": SesTerminalError,
    "AccessDeniedException": SesAuthError,
    "UnauthorizedOperation": SesAuthError,
    "ValidationException": SesTerminalError,
}

_TRANSIENT_CODE_MAP: dict[str, type[SesTransientError]] = {
    "Throttling": SesThrottlingError,
    "ThrottlingException": SesThrottlingError,
    "TooManyRequestsException": SesThrottlingError,
    "ServiceUnavailable": SesTransientError,
    "ServiceUnavailableException": SesTransientError,
    "RequestTimeout": SesTransientError,
    "RequestTimeoutException": SesTransientError,
    "InternalFailure": SesTransientError,
    "InternalError": SesTransientError,
}


def map_ses_error(*, code: str, message: str) -> SesError:
    transient = _TRANSIENT_CODE_MAP.get(code)
    if transient is not None:
        return transient(message)

    terminal = _TERMINAL_CODE_MAP.get(code)
    if terminal is not None:
        return terminal(message)

    return SesTerminalError(message)
