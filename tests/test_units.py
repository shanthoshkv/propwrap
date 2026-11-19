def test_temperature_direct_conversions():
    import pytest
    from propwrap.units import convert
    assert convert(100, 'C', 'F') == pytest.approx(212.0)
