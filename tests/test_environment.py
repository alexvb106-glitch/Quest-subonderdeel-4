import sys


# Controleer dat de draaiende interpreter voldoet aan requires-python (>= 3.14)
def test_python_version_is_at_least_3_14():
    assert sys.version_info >= (3, 14)
