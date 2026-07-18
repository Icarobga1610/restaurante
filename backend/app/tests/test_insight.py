"""Regression tests for cross-dialect insight queries."""


def test_insight_endpoints_work_with_sqlite(client, auth_header):
    endpoints = [
        "/api/insights/seasonality/top-products-day",
        "/api/insights/seasonality/top-products-month",
        "/api/insights/seasonality/peak-hours",
        "/api/insights/refresh",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint, headers=auth_header)
        assert response.status_code == 200, (endpoint, response.text)
