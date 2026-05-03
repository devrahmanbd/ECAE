from math_api import calculate_ratio

def test_calculate_ratio_normal():
    assert calculate_ratio(10, 2) == 5.0

def test_calculate_ratio_zero_denominator():
    # This should return 1.0 based on our mock fix logic
    assert calculate_ratio(1, 0) == 1.0
