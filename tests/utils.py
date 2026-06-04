def response_data(response):
    if response.status_code == 204:
        return None
    return response.json()


def results(data):
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    return data


def assert_not_server_error(response):
    assert response.status_code < 500, response.content.decode()


def assert_missing_or_method_not_allowed(response):
    assert_not_server_error(response)
    assert response.status_code in (404, 405)
