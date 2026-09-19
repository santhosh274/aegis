from evaluation.scripts.collect_metrics import (
    accuracy,
    confusion,
    false_all_clear_rate,
)


def test_accuracy_perfect():
    assert accuracy(["confirmed", "suspected"], ["confirmed", "suspected"]) == 1.0


def test_accuracy_partial():
    assert accuracy(["confirmed", "confirmed"], ["confirmed", "suspected"]) == 0.5


def test_accuracy_empty():
    assert accuracy([], []) == 0.0


def test_confusion_matrix_keys():
    result = confusion(["confirmed", "suspected"], ["confirmed", "confirmed"])
    assert result[("confirmed", "confirmed")] == 1
    assert result[("suspected", "confirmed")] == 1


def test_false_all_clear_rate_zero_when_correct():
    assert false_all_clear_rate([False, False], ["verified_closed", "verified_closed"]) == 0.0


def test_false_all_clear_rate_catches_bad_verdict():
    assert false_all_clear_rate([True, False], ["verified_closed", "verified_closed"]) == 0.5


def test_false_all_clear_rate_empty():
    assert false_all_clear_rate([], []) == 0.0
