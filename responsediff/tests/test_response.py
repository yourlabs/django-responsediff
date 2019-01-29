from responsediff import Response


def test_response(client):
    """Check that csrf_token was replaced and that the thing works."""
    res = client.get('/admin/login/')
    Response('mrsrequest/tests/responses/test_response').assertNoDiff(res)
