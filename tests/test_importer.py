import pytest

from temporalloop.importer import ImportFromStringError, import_from_string
from temporalloop.utils import time_interval
from temporalloop.worker import Looper


def test_import_from_string_success():
    """Test successful import of a function."""
    func = import_from_string("temporalloop.utils:time_interval")
    assert func is time_interval


def test_import_from_string_class_success():
    """Test successful import of a class."""
    cls = import_from_string("temporalloop.worker:Looper")
    assert cls is Looper


def test_import_from_string_invalid_format():
    """Test invalid import string format."""
    with pytest.raises(
        ImportFromStringError, match=r'Import string "invalid" must be in format "<module>:<attribute>".'
    ):
        import_from_string("invalid")


def test_import_from_string_module_not_found():
    """Test import from a non-existent module."""
    with pytest.raises(ImportFromStringError, match=r'Could not import module "non_existent_module".'):
        import_from_string("non_existent_module:some_function")


def test_import_from_string_attribute_not_found():
    """Test import of a non-existent attribute."""
    with pytest.raises(
        ImportFromStringError, match=r'Attribute "non_existent_function" not found in module "temporalloop.utils".'
    ):
        import_from_string("temporalloop.utils:non_existent_function")


def test_import_from_string_non_string_input():
    """Test passing a non-string input."""
    obj = object()
    assert import_from_string(obj) is obj
