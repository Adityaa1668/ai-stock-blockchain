import pandas as pd

from backend.analyzer import analyze_prices, demo_prices, dtw_distance, prediction_fingerprint


def test_dtw_identical_sequences_have_zero_distance():
    assert dtw_distance([1, 2, 3], [1, 2, 3]) == 0


def test_demo_analysis_is_deterministic():
    first = analyze_prices(demo_prices(), "DEMO")
    second = analyze_prices(demo_prices(), "DEMO")
    assert first.signal in {"BUY", "HOLD", "SELL"}
    assert first.prediction_hash == second.prediction_hash
    assert len(first.matches) == 5


def test_hash_ignores_dictionary_order():
    assert prediction_fingerprint({"a": 1, "b": 2}) == prediction_fingerprint({"b": 2, "a": 1})


def test_too_little_data_is_rejected():
    frame = pd.DataFrame({"Close": range(25)})
    try:
        analyze_prices(frame, "SHORT")
    except ValueError as error:
        assert "At least" in str(error)
    else:
        raise AssertionError("Expected short data to be rejected")

