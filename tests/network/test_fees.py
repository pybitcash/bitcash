import pytest

from bitcash.network.fees import get_fee


def test_get_fee():
    assert get_fee(speed='fast') >= get_fee(speed='medium')
    assert get_fee(speed='medium') >= get_fee(speed='slow')


def test_get_fee_invalid_speed():
    with pytest.raises(ValueError):
        get_fee(speed='super fast')
