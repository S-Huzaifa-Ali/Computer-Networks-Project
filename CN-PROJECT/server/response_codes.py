SERVICE_READY = 220
SERVICE_CLOSING = 221
AUTH_SUCCESS = 235
OK = 250
START_MAIL_INPUT = 354

SERVICE_UNAVAILABLE = 421
MAILBOX_TEMP_UNAVAIL = 450
SYNTAX_ERROR = 500
ARGUMENT_ERROR = 501
BAD_SEQUENCE = 503
MAILBOX_NOT_FOUND = 550
AUTH_FAILED = 535

MESSAGES = {
    220: "Service ready",
    221: "Service closing transmission channel",
    235: "Authentication successful",
    250: "OK",
    354: "Start mail input; end with <CRLF>.<CRLF>",
    421: "Service not available, closing transmission channel",
    450: "Requested mail action not taken: mailbox unavailable",
    500: "Syntax error, command unrecognized",
    501: "Syntax error in parameters or arguments",
    503: "Bad sequence of commands",
    550: "Requested action not taken: mailbox unavailable",
    535: "Authentication credentials invalid",
}


def build_response(code, custom_message=None):
    """
    Build an SMTP response string.
    Format: '250 OK\r\n'
    """
    message = custom_message if custom_message else MESSAGES.get(code, "")
    return f"{code} {message}\r\n"


def build_multiline_response(code, lines):
    """
    Build a multi-line SMTP response (used for EHLO capabilities).
    All lines except the last use 'code-' prefix,
    the last line uses 'code ' prefix.
    """
    if not lines:
        return build_response(code)

    result = ""
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            result += f"{code}-{line}\r\n"
        else:
            result += f"{code} {line}\r\n"
    return result
