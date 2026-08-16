from riverview.spatial.prototype import prototype_html


def test_spatial_prototype_is_webxr_capable_but_read_only() -> None:
    html = prototype_html()
    assert "navigator.xr" in html
    assert "immersive-vr" in html
    assert "PROPOSED" in html
    assert "operational controls remain disabled" in html
