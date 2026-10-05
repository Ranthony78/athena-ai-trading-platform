import json
import math

from django.test import SimpleTestCase

from .indicators.indicator_service import json_safe


class JsonSafeTests(SimpleTestCase):

    def test_nan_and_infinity_become_none(self):
        data = {"RSI_14": [float("nan"), 50.5, float("inf"), -float("inf")]}
        self.assertEqual(json_safe(data), {"RSI_14": [None, 50.5, None, None]})

    def test_nested_structures_are_cleaned(self):
        data = {"BB_20": {"upper": [math.nan, 1.5], "lower": [math.nan, 0.5]}, "k": 3}
        self.assertEqual(
            json_safe(data),
            {"BB_20": {"upper": [None, 1.5], "lower": [None, 0.5]}, "k": 3},
        )

    def test_real_numbers_text_and_none_are_untouched(self):
        data = {"a": [1, 2.5, None, "x", True], "error": "No candle data"}
        self.assertEqual(json_safe(data), data)

    def test_the_result_is_strict_json(self):
        cleaned = json_safe({"x": [math.nan, 1.0]})
        # allow_nan=False is what Django REST framework uses.
        self.assertEqual(json.dumps(cleaned, allow_nan=False), '{"x": [null, 1.0]}')

    def test_does_not_change_its_input(self):
        data = {"x": [math.nan]}
        json_safe(data)
        self.assertTrue(math.isnan(data["x"][0]))
