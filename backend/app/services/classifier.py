"""Classification parser: extracts and categorizes Moneycontrol stock classifications."""

import re
from html import unescape
from typing import Optional, Tuple
from enum import Enum


class MatchedCategory(str, Enum):
    AVERAGE_DISCOUNTED = "AVERAGE_DISCOUNTED"
    AVERAGE_ATTRACTIVE = "AVERAGE_ATTRACTIVE"
    HIGH_ATTRACTIVE = "HIGH_ATTRACTIVE"
    HIGH_REASONABLE = "HIGH_REASONABLE"
    HIGH_HIGH_VALUATION = "HIGH_HIGH_VALUATION"


# The five target classifications
TARGET_CATEGORIES = {
    MatchedCategory.AVERAGE_DISCOUNTED: {
        'growth': 'average',
        'valuation': 'discounted',
        'label': 'Average Growth Trend Stock at Discounted Valuations',
        'short_label': 'Average Growth · Discounted Valuation',
    },
    MatchedCategory.AVERAGE_ATTRACTIVE: {
        'growth': 'average',
        'valuation': 'attractive',
        'label': 'Average Growth Trend Stock at Attractive Valuations',
        'short_label': 'Average Growth · Attractive Valuation',
    },
    MatchedCategory.HIGH_ATTRACTIVE: {
        'growth': 'high',
        'valuation': 'attractive',
        'label': 'High Growth Trend Stock at Attractive Valuations',
        'short_label': 'High Growth · Attractive Valuation',
    },
    MatchedCategory.HIGH_REASONABLE: {
        'growth': 'high',
        'valuation': 'reasonable',
        'label': 'High Growth Trend Stock at Reasonable Valuations',
        'short_label': 'High Growth · Reasonable Valuation',
    },
    MatchedCategory.HIGH_HIGH_VALUATION: {
        'growth': 'high',
        'valuation': 'high',
        'label': 'High Growth Trend Stock Priced at High Valuations',
        'short_label': 'High Growth · High Valuation',
    },
}

class ClassifierService:
    """Parses and classifies Moneycontrol stock score classification text."""

    @staticmethod
    def normalize_text(raw_text: str) -> str:
        """Normalize classification text for reliable parsing."""
        if not raw_text:
            return ''
        text = unescape(raw_text)
        text = re.sub(r'<[^>]+>', '', text)  # Strip HTML tags
        text = re.sub(r'\s+', ' ', text)     # Collapse whitespace
        text = text.strip()
        return text

    @staticmethod
    def classify(raw_text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Parse a classification string and determine the matched category."""
        if not raw_text:
            return None, None, None, None

        text = ClassifierService.normalize_text(raw_text)

        pattern = (
            r'(\w[\w\s]*?Financial\s+Strength)'  
            r'[,\s]+'                              
            r'(\w[\w\s]*?Growth\s+Trend\s+Stock)'  
            r'\s+'
            r'(?:at|Priced\s+at)\s+'               
            r'(\w[\w\s]*?Valuations?)'              
        )

        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            alt_pattern = (
                r'(\w[\w\s]*?Financial\s+Strength)'
                r'[,\s]+'
                r'(\w[\w\s]*?Growth\s+Trend)'
                r'\s+'
                r'(?:at|Priced\s+at)\s+'
                r'(\w[\w\s]*?Valuations?)'
            )
            match = re.search(alt_pattern, text, re.IGNORECASE)

        if not match:
            return None, None, None, None

        financial_strength = match.group(1).strip()
        growth_trend = match.group(2).strip()
        valuation = match.group(3).strip()

        growth_lower = growth_trend.lower()
        val_lower = valuation.lower()

        category = None

        growth_level = None
        if 'high' in growth_lower.split() or growth_lower.startswith('high'):
            growth_level = 'high'
        elif 'average' in growth_lower.split() or growth_lower.startswith('average'):
            growth_level = 'average'

        val_level = None
        if 'discounted' in val_lower:
            val_level = 'discounted'
        elif 'attractive' in val_lower:
            val_level = 'attractive'
        elif 'reasonable' in val_lower:
            val_level = 'reasonable'
        elif 'high' in val_lower.split():
            val_level = 'high'

        for cat, criteria in TARGET_CATEGORIES.items():
            if growth_level == criteria['growth'] and val_level == criteria['valuation']:
                category = cat.value
                break

        return financial_strength, growth_trend, valuation, category

    @staticmethod
    def is_qualified(category: Optional[str]) -> bool:
        """Check if a category is one of the four target categories."""
        if not category:
            return False
        try:
            MatchedCategory(category)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_category_info(category: str) -> Optional[dict]:
        """Get label and display info for a category."""
        try:
            cat = MatchedCategory(category)
            return TARGET_CATEGORIES.get(cat)
        except (ValueError, KeyError):
            return None

    @staticmethod
    def get_rejection_reason(growth_trend: Optional[str], valuation: Optional[str]) -> str:
        """Generate a human-readable reason for why a stock didn't qualify."""
        if not growth_trend and not valuation:
            return "Classification could not be parsed"

        reasons = []
        growth_lower = (growth_trend or '').lower()
        val_lower = (valuation or '').lower()

        # Check growth
        if 'high' not in growth_lower and 'average' not in growth_lower:
            reasons.append(f"Growth trend '{growth_trend}' is not Average or High")

        # Check valuation
        valid_vals = ['discounted', 'attractive', 'high']
        if not any(v in val_lower for v in valid_vals):
            reasons.append(f"Valuation '{valuation}' is not Discounted, Attractive, or High")

        # If both are valid individually but the combination doesn't match
        if not reasons:
            reasons.append(f"Combination of '{growth_trend}' + '{valuation}' does not match any target category")

        return "; ".join(reasons)
