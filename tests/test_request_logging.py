from app.middleware.request_logging import _redacted_query
from starlette.requests import Request


def _request_with_query(query_string: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": query_string.encode(),
        "headers": [],
    }
    return Request(scope)


def test_secret_param_is_redacted():
    req = _request_with_query("secret=super-secret-value&eid=123&cid=click-1")
    result = _redacted_query(req)
    assert "super-secret-value" not in result
    assert "secret=***" in result
    assert "eid=123" in result
    assert "cid=click-1" in result


def test_no_query_params_returns_empty_string():
    req = _request_with_query("")
    assert _redacted_query(req) == ""


def test_non_sensitive_params_untouched():
    req = _request_with_query("geo=SY&status=active")
    result = _redacted_query(req)
    assert result == "geo=SY&status=active"
