"""
Unit tests for data preprocessing and input validation.
"""
import pytest
import numpy as np

from backend.ml.preprocessor import validate_prediction_input, FEATURE_COLUMNS, SCALE_COLUMNS


def test_validate_prediction_input_valid():
    """Verify valid input dict returns array with correct order and length."""
    sample = {col: 0.5 for col in FEATURE_COLUMNS}
    arr = validate_prediction_input(sample)
    assert isinstance(arr, np.ndarray)
    assert len(arr) == len(FEATURE_COLUMNS)
    assert arr[FEATURE_COLUMNS.index("Time")] == 0.5
    assert arr[FEATURE_COLUMNS.index("Amount")] == 0.5


def test_validate_prediction_input_missing_field():
    """Verify validation raises ValueError when required feature is missing."""
    sample = {col: 0.5 for col in FEATURE_COLUMNS}
    del sample["Amount"]
    with pytest.raises(ValueError, match="Missing required features"):
        validate_prediction_input(sample)


def test_validate_prediction_input_nan():
    """Verify validation rejects NaN values."""
    sample = {col: 0.5 for col in FEATURE_COLUMNS}
    sample["V1"] = float("nan")
    with pytest.raises(ValueError, match="non-finite value"):
        validate_prediction_input(sample)


def test_scale_columns():
    """Verify only Time and Amount are designated for scaling."""
    assert "Time" in SCALE_COLUMNS
    assert "Amount" in SCALE_COLUMNS
    assert len(SCALE_COLUMNS) == 2
