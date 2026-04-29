import pytest
from worker.processor import process


def test_uppercase():
    assert process('uppercase', 'hello') == 'HELLO'


def test_lowercase():
    assert process('lowercase', 'HeLLo') == 'hello'


def test_reverse():
    assert process('reverse', 'abc') == 'cba'


def test_wordcount():
    assert process('wordcount', 'one two  three') == {'count': 3}


def test_unknown():
    with pytest.raises(ValueError):
        process('invalid', 'x')
