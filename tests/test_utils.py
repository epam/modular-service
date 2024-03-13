import pytest

from commons import deep_get, deep_set, dereference_json, urljoin


@pytest.fixture
def dictionary() -> dict:
    """
    Generates some more or less complex dictionary to test related method on
    :return:
    """
    return {
        'one': 'two',
        3: {
            'four': 'five'
        },
        'six': {
            'seven': {'eight': 'nine'}
        },
        'ten': [{
            'eleven': 'twelve'
        }]
    }


def test_deep_get(dictionary):
    assert deep_get(dictionary, ('one',)) == 'two'
    assert deep_get(dictionary, (3, 'four')) == 'five'
    assert deep_get(dictionary, ('six', 'seven', 'eight')) == 'nine'
    assert deep_get(dictionary, ('six', 'seven', 'ten')) is None


def test_deep_set():
    a = {}
    deep_set(a, ('one', 'two', 'three'), 'candy')
    deep_set(a, (1, 2, 3), 'candy')
    assert a['one']['two']['three'] == 'candy'
    assert a[1][2][3] == 'candy'


def test_urljoin():
    assert urljoin('one', 'two', 'three') == 'one/two/three'
    assert urljoin('/one/', '/two/', '/three/') == 'one/two/three'
    assert urljoin('/one', 'two', 'three/') == 'one/two/three'
    assert urljoin('/one/') == 'one'


def test_dereference_json():
    obj = {
        'key1': {
            'a': [1, 2, 3],
            'b': {'$ref': '#/key3'}
        },
        'key2': {
            '$ref': '#/key1',
        },
        'key3': 10
    }
    dereference_json(obj)
    # obj = jsonref.replace_refs(obj, lazy_load=False)
    assert obj == {
        'key1': {'a': [1, 2, 3], 'b': 10},
        'key2': {'a': [1, 2, 3], 'b': 10},
        'key3': 10
    }

    obj = {
        'key0': {'$ref': '#/key1/value'},
        'key1': {'value': 1, 'test': {'$ref': '#/key2'}},
        'key2': [1, 2, 3],
        'key4': [1, 2, {'test': {'$ref': '#/key0'}}]
    }
    dereference_json(obj)
    # obj = jsonref.replace_refs(obj, lazy_load=False)
    assert obj == {
        'key0': 1,
        'key1': {'value': 1, 'test': [1, 2, 3]},
        'key2': [1, 2, 3],
        'key4': [1, 2, {'test': 1}]
    }
