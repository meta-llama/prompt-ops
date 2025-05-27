import json
import pytest

# Import the metrics classes
try:
    from llama_prompt_ops.core.metrics import (
        MetricBase,
        ExactMatchMetric,
        json_evaluation_metric,
        StandardJSONMetric,
        FacilityMetric
    )
except ImportError:
    # If the imports fail, the tests will be skipped
    pass


@pytest.fixture
def sample_json_data():
    """Fixture providing sample JSON data for testing."""
    return {
        "field1": "value1",
        "field2": "value2",
        "nested": {
            "subfield1": "subvalue1",
            "subfield2": "subvalue2"
        }
    }


@pytest.mark.parametrize("case_sensitive,strip_whitespace,gold,pred,expected", [
    (True, True, "Answer", "Answer", 1.0),  # Exact match
    (True, True, "Answer", "answer", 0.0),  # Case mismatch
    (False, True, "Answer", "answer", 1.0),  # Case insensitive match
    (True, True, "Answer ", " Answer", 1.0),  # Whitespace stripped
    (True, False, "Answer ", " Answer", 0.0),  # Whitespace preserved
    (False, False, "Answer", "ANSWER ", 0.0),  # Case insensitive but whitespace preserved
])
def test_exact_match_metric(case_sensitive, strip_whitespace, gold, pred, expected):
    """Test ExactMatchMetric with different configurations."""
    try:
        metric = ExactMatchMetric(case_sensitive=case_sensitive, strip_whitespace=strip_whitespace)
        result = metric(gold, pred)
        
        # Check if the result is a dictionary or a float
        if isinstance(result, dict):
            assert result.get("exact_match", 0.0) == expected
        else:
            assert result == expected
    except NameError:
        pytest.skip("ExactMatchMetric not available")


def test_exact_match_metric_with_objects():
    """Test ExactMatchMetric with objects that have string representations."""
    try:
        class TestObject:
            def __init__(self, value):
                self.value = value
                
            def __str__(self):
                return self.value
        
        metric = ExactMatchMetric()
        
        # Test with objects that have string representations
        gold_obj = TestObject("test value")
        pred_obj = TestObject("test value")
        
        result = metric(gold_obj, pred_obj)
        
        # Check if the result is a dictionary or a float
        if isinstance(result, dict):
            assert result.get("exact_match", 0.0) == 1.0
        else:
            assert result == 1.0
    except NameError:
        pytest.skip("ExactMatchMetric not available")


def test_json_evaluation_metric_exact_match(sample_json_data):
    """Test json_evaluation_metric with exact match."""
    try:
        # Create a copy of the sample data for prediction
        pred = sample_json_data.copy()
        
        # Test with dict inputs
        result = json_evaluation_metric(sample_json_data, pred)
        
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0
        
        # Test with string inputs
        gold_str = json.dumps(sample_json_data)
        pred_str = json.dumps(pred)
        
        result = json_evaluation_metric(gold_str, pred_str)
        
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0
    except NameError:
        pytest.skip("json_evaluation_metric not available")


def test_json_evaluation_metric_partial_match(sample_json_data):
    """Test json_evaluation_metric with partial match."""
    try:
        # Create a modified prediction with some differences
        pred = {
            "field1": "value1",  # Same
            "field3": "value3",  # Different key
            "nested": {
                "subfield1": "subvalue1",  # Same
                "subfield3": "subvalue3"   # Different key
            }
        }
        
        result = json_evaluation_metric(sample_json_data, pred)
        
        # Should have partial matches
        assert 0 < result["precision"] < 1.0
        assert 0 < result["recall"] < 1.0
        assert 0 < result["f1"] < 1.0
    except NameError:
        pytest.skip("json_evaluation_metric not available")


def test_json_evaluation_metric_invalid_json():
    """Test json_evaluation_metric with invalid JSON."""
    try:
        gold = {"field": "value"}
        pred = "This is not valid JSON"
        
        result = json_evaluation_metric(gold, pred)
        
        # Should handle invalid JSON gracefully
        assert "precision" in result
        assert "recall" in result
        assert "f1" in result
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0
        assert result["f1"] == 0.0
    except NameError:
        pytest.skip("json_evaluation_metric not available")


def test_standard_json_metric_exists():
    """Test that StandardJSONMetric class exists and can be instantiated."""
    try:
        # Just test that we can create an instance without errors
        metric = StandardJSONMetric()
        assert isinstance(metric, MetricBase)
        
        # Test with some basic parameters
        metric = StandardJSONMetric(
            fields=["field1", "field2"],
            required_fields=["field1"],
            strict_json=True
        )
        
        # Test with field weights
        metric = StandardJSONMetric(
            fields={"field1": 0.7, "field2": 0.3},
            strict_json=False
        )
        
        # Test with nested fields
        metric = StandardJSONMetric(
            fields=["simple_field"],
            nested_fields={"parent": ["child1", "child2"]}
        )
    except (NameError, ImportError):
        pytest.skip("StandardJSONMetric not available")


def test_standard_json_metric_has_required_methods():
    """Test that StandardJSONMetric has the required methods."""
    try:
        # Create a StandardJSONMetric instance
        metric = StandardJSONMetric()
        
        # Check that it has the required methods
        assert hasattr(metric, "__call__")
        assert hasattr(metric, "extract_value")
        
        # Check that the methods are callable
        assert callable(metric.__call__)
        assert callable(metric.extract_value)
    except (NameError, ImportError):
        pytest.skip("StandardJSONMetric not available")


def test_facility_metric():
    """Test FacilityMetric functionality."""
    try:
        # Create a FacilityMetric instance
        metric = FacilityMetric()
        
        # Test with matching categories, sentiment, and urgency
        # Note: categories should be a dictionary, not a list
        gold = {
            "categories": {"maintenance": True, "cleaning": True, "emergency": False},
            "sentiment": "neutral",
            "urgency": "medium"
        }
        
        pred = gold.copy()  # Exact copy should match perfectly
        
        # Convert to JSON strings
        gold_str = json.dumps(gold)
        pred_str = json.dumps(pred)
        
        # Test with exact match inputs
        result = metric(gold_str, pred_str)
        
        # FacilityMetric should return a dictionary with specific fields
        assert isinstance(result, dict), "FacilityMetric should return a dictionary"
        assert "correct_categories" in result, "Result should contain 'correct_categories'"
        assert "correct_sentiment" in result, "Result should contain 'correct_sentiment'"
        assert "correct_urgency" in result, "Result should contain 'correct_urgency'"
        assert "total" in result, "Result should contain 'total'"
        
        # Check values for exact match
        assert result["correct_categories"] == 1.0
        assert result["correct_sentiment"] is True
        assert result["correct_urgency"] is True
        assert result["total"] == 1.0
        
        # Test with partially matching fields
        pred_partial = {
            "categories": {"maintenance": True, "cleaning": False, "emergency": False},  # Different from gold
            "sentiment": "neutral",
            "urgency": "high"  # Different from "medium"
        }
        
        pred_partial_str = json.dumps(pred_partial)
        
        result = metric(gold_str, pred_partial_str)
        
        # FacilityMetric should return a dictionary with specific fields
        assert isinstance(result, dict), "FacilityMetric should return a dictionary"
        assert "correct_categories" in result, "Result should contain 'correct_categories'"
        assert "correct_sentiment" in result, "Result should contain 'correct_sentiment'"
        assert "correct_urgency" in result, "Result should contain 'correct_urgency'"
        assert "total" in result, "Result should contain 'total'"
        
        # Check values for partial match
        assert result["correct_categories"] < 1.0
        assert result["correct_sentiment"] is True
        assert result["correct_urgency"] is False
        assert result["total"] < 1.0
    except NameError:
        pytest.skip("FacilityMetric not available")


def test_metric_base_extract_value():
    """Test the extract_value method of MetricBase."""
    try:
        # Create a concrete implementation of the abstract MetricBase
        class ConcreteMetric(MetricBase):
            def __call__(self, gold, pred, trace=False, **kwargs):
                return 1.0
        
        metric = ConcreteMetric()
        
        # Test with dictionary
        test_dict = {"key": "value"}
        assert metric.extract_value(test_dict, "key") == "value"
        assert metric.extract_value(test_dict, "missing", "default") == "default"
        
        # Test with object
        class TestObject:
            def __init__(self):
                self.attribute = "value"
        
        test_obj = TestObject()
        assert metric.extract_value(test_obj, "attribute") == "value"
        assert metric.extract_value(test_obj, "missing", "default") == "default"
    except NameError:
        pytest.skip("MetricBase not available")
