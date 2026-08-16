from pathlib import Path

import pytest

from riverview.operator.lan_spatial import build_server


def test_lan_spatial_rejects_loopback() -> None:
    with pytest.raises(ValueError, match="loopback"):
        build_server(host="127.0.0.1", port=18444, cert_dir=Path("runtime/test-tls"))
