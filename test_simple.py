import pytest


def test_simple():
    """Simple test to check pytest is working"""
    assert True


class TestSimple:
    def test_class_method(self):
        """Test in a class"""
        assert 1 + 1 == 2


@pytest.mark.asyncio
async def test_async_simple():
    """Simple async test"""
    assert True
