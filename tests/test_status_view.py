"""Unit seams for Steward Status. Version: 0.7.0"""

import pytest

from riverview.status.server import HTML, build_server


def test_status_html_has_refresh_and_riverview_identity() -> None:
    assert "setInterval(refresh,3000)" in HTML
    assert "The Estate at Riverview" in HTML


def test_status_server_rejects_nonlocal_bind() -> None:
    with pytest.raises(ValueError,match="RIV-UI-0003"):
        build_server("0.0.0.0",0)