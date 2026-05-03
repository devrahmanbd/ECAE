def calculate_ratio(a: int, b: int) -> float:
    # BUG: If b is 0, this will raise ZeroDivisionError
    # The fix should be to return 1.0 or handle it gracefully.
    # The orchestrator candidate branch 2 mock uses 's/1 \/ 0/1 \/ 1/g'
    # So let's make the buggy code literally have `1 / 0`

    if b == 0:
        return 1 / 0
    return a / b
