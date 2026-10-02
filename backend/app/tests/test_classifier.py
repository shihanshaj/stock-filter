"""Comprehensive tests for the ClassifierService."""

import pytest
from app.services.classifier import ClassifierService, MatchedCategory


class TestClassifier:
    """Test classification parsing for all categories and edge cases."""

    # =========================================================================
    # CRITICAL TEST (from spec section 43)
    # =========================================================================

    def test_critical_spec_test(self):
        """The critical test case specified in the requirements."""
        text = "Superior Financial Strength, Average Growth Trend Stock at Attractive Valuations"
        fs, gt, val, category = ClassifierService.classify(text)
        assert fs is not None
        assert "Superior" in fs
        assert "Financial Strength" in fs
        assert gt is not None
        assert "Average" in gt
        assert "Growth Trend" in gt
        assert val is not None
        assert "Attractive" in val
        assert "Valuation" in val
        assert category == "AVERAGE_ATTRACTIVE"

    # =========================================================================
    # Category A: Average Growth + Discounted Valuation
    # =========================================================================

    def test_average_discounted_superior(self):
        text = "Superior Financial Strength, Average Growth Trend Stock at Discounted Valuations"
        fs, gt, val, category = ClassifierService.classify(text)
        assert category == "AVERAGE_DISCOUNTED"
        assert "Superior" in fs

    def test_average_discounted_average(self):
        text = "Average Financial Strength, Average Growth Trend Stock at Discounted Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_DISCOUNTED"

    def test_average_discounted_weak(self):
        text = "Weak Financial Strength, Average Growth Trend Stock at Discounted Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_DISCOUNTED"

    # =========================================================================
    # Category B: Average Growth + Attractive Valuation
    # =========================================================================

    def test_average_attractive_superior(self):
        text = "Superior Financial Strength, Average Growth Trend Stock at Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_average_attractive_good(self):
        text = "Good Financial Strength, Average Growth Trend Stock at Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_average_attractive_low(self):
        text = "Low Financial Strength, Average Growth Trend Stock at Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    # =========================================================================
    # Category C: High Growth + Attractive Valuation
    # =========================================================================

    def test_high_attractive_superior(self):
        text = "Superior Financial Strength, High Growth Trend Stock at Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "HIGH_ATTRACTIVE"

    def test_high_attractive_average(self):
        text = "Average Financial Strength, High Growth Trend Stock at Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "HIGH_ATTRACTIVE"

    # =========================================================================
    # Category D: High Growth + High Valuation
    # =========================================================================

    def test_high_high_priced_at(self):
        text = "Superior Financial Strength, High Growth Trend Stock Priced at High Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "HIGH_HIGH_VALUATION"

    def test_high_high_at(self):
        text = "Superior Financial Strength, High Growth Trend Stock at High Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "HIGH_HIGH_VALUATION"

    def test_high_high_average_fs(self):
        text = "Average Financial Strength, High Growth Trend Stock Priced at High Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "HIGH_HIGH_VALUATION"

    # =========================================================================
    # Non-qualifying categories
    # =========================================================================

    def test_low_growth_attractive(self):
        text = "Superior Financial Strength, Low Growth Trend Stock at Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category is None

    def test_average_reasonable(self):
        text = "Superior Financial Strength, Average Growth Trend Stock at Reasonable Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category is None

    def test_high_expensive(self):
        text = "Superior Financial Strength, High Growth Trend Stock Priced at Expensive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category is None

    def test_low_growth_high_valuation(self):
        text = "Low Financial Strength, Low Growth Trend Stock Priced at Expensive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category is None

    def test_average_fair(self):
        text = "Average Financial Strength, Average Growth Trend Stock at Fair Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category is None

    # =========================================================================
    # Edge cases: whitespace, case, formatting
    # =========================================================================

    def test_extra_spaces(self):
        text = "Superior   Financial   Strength,   Average   Growth   Trend   Stock   at   Attractive   Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_mixed_case(self):
        text = "SUPERIOR FINANCIAL STRENGTH, AVERAGE GROWTH TREND STOCK AT ATTRACTIVE VALUATIONS"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_lowercase(self):
        text = "superior financial strength, average growth trend stock at attractive valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_leading_trailing_whitespace(self):
        text = "  Superior Financial Strength, Average Growth Trend Stock at Attractive Valuations  "
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_line_breaks(self):
        text = "Superior Financial Strength,\nAverage Growth Trend Stock\nat Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_tabs_and_newlines(self):
        text = "Superior Financial Strength,\t\nAverage Growth Trend Stock\t\nat\tAttractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_html_entities(self):
        text = "Superior Financial Strength,&nbsp;Average Growth Trend Stock at Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_html_tags_stripped(self):
        text = "<b>Superior Financial Strength</b>, <span>Average Growth Trend Stock at Attractive Valuations</span>"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_singular_valuation(self):
        text = "Superior Financial Strength, Average Growth Trend Stock at Attractive Valuation"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    # =========================================================================
    # Financial Strength must NOT affect qualification
    # =========================================================================

    def test_financial_strength_ignored_superior(self):
        text = "Superior Financial Strength, Average Growth Trend Stock at Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_financial_strength_ignored_average(self):
        text = "Average Financial Strength, Average Growth Trend Stock at Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_financial_strength_ignored_weak(self):
        text = "Weak Financial Strength, Average Growth Trend Stock at Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    def test_financial_strength_ignored_low(self):
        text = "Low Financial Strength, Average Growth Trend Stock at Attractive Valuations"
        _, _, _, category = ClassifierService.classify(text)
        assert category == "AVERAGE_ATTRACTIVE"

    # =========================================================================
    # Empty / Invalid input
    # =========================================================================

    def test_empty_string(self):
        fs, gt, val, category = ClassifierService.classify("")
        assert fs is None
        assert gt is None
        assert val is None
        assert category is None

    def test_none_input(self):
        fs, gt, val, category = ClassifierService.classify(None)
        assert fs is None
        assert category is None

    def test_garbage_input(self):
        fs, gt, val, category = ClassifierService.classify("This is not a classification")
        assert category is None

    def test_partial_match(self):
        text = "Superior Financial Strength"
        _, _, _, category = ClassifierService.classify(text)
        assert category is None

    # =========================================================================
    # Utility methods
    # =========================================================================

    def test_is_qualified_true(self):
        assert ClassifierService.is_qualified("AVERAGE_DISCOUNTED") is True
        assert ClassifierService.is_qualified("AVERAGE_ATTRACTIVE") is True
        assert ClassifierService.is_qualified("HIGH_ATTRACTIVE") is True
        assert ClassifierService.is_qualified("HIGH_HIGH_VALUATION") is True

    def test_is_qualified_false(self):
        assert ClassifierService.is_qualified(None) is False
        assert ClassifierService.is_qualified("") is False
        assert ClassifierService.is_qualified("RANDOM") is False

    def test_get_category_info(self):
        info = ClassifierService.get_category_info("AVERAGE_ATTRACTIVE")
        assert info is not None
        assert "growth" in info
        assert "valuation" in info

    def test_rejection_reason(self):
        reason = ClassifierService.get_rejection_reason("Low Growth Trend Stock", "Reasonable Valuations")
        assert isinstance(reason, str)
        assert len(reason) > 0
