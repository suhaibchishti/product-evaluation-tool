#!/usr/bin/env python3
"""Unit tests for the product evaluation engine."""

import json
import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from evaluate import (
    parse_rating,
    normalize_ratings,
    normalize_weights,
    score_tool,
    rank_tools,
    analyze_sensitivity,
    detect_flips,
    validate_inputs,
    criteria_name_map,
    format_markdown,
    format_csv,
    format_terminal,
)


# ─── parse_rating ────────────────────────────────────────────────────────────

class TestParseRating:
    def test_plain_int(self):
        assert parse_rating(3) == (3, None, None)

    def test_plain_float(self):
        assert parse_rating(4.5) == (4.5, None, None)

    def test_dict_full(self):
        val = {"score": 4, "confidence": 5, "note": "Good docs"}
        assert parse_rating(val) == (4, 5, "Good docs")

    def test_dict_score_only(self):
        val = {"score": 3}
        assert parse_rating(val) == (3, None, None)

    def test_dict_missing_score(self):
        val = {"confidence": 2}
        assert parse_rating(val) == (0, 2, None)


# ─── normalize_ratings ───────────────────────────────────────────────────────

class TestNormalizeRatings:
    def test_plain_ratings(self):
        raw = {"tool_a": {"x": 3, "y": 5}}
        scores, conf, notes = normalize_ratings(raw)
        assert scores == {"tool_a": {"x": 3, "y": 5}}
        assert conf == {"tool_a": {"x": None, "y": None}}
        assert notes == {"tool_a": {"x": None, "y": None}}

    def test_dict_ratings(self):
        raw = {"tool_a": {"x": {"score": 4, "confidence": 3, "note": "ok"}}}
        scores, conf, notes = normalize_ratings(raw)
        assert scores == {"tool_a": {"x": 4}}
        assert conf == {"tool_a": {"x": 3}}
        assert notes == {"tool_a": {"x": "ok"}}

    def test_mixed_ratings(self):
        raw = {"tool_a": {"x": 3, "y": {"score": 5, "confidence": 4, "note": "great"}}}
        scores, conf, notes = normalize_ratings(raw)
        assert scores["tool_a"]["x"] == 3
        assert scores["tool_a"]["y"] == 5
        assert conf["tool_a"]["x"] is None
        assert conf["tool_a"]["y"] == 4


# ─── normalize_weights ──────────────────────────────────────────────────────

class TestNormalizeWeights:
    def test_basic(self):
        w = {"a": 2, "b": 3}
        nw = normalize_weights(w)
        assert abs(nw["a"] - 0.4) < 1e-9
        assert abs(nw["b"] - 0.6) < 1e-9

    def test_sums_to_one(self):
        w = {"a": 1, "b": 2, "c": 3, "d": 4}
        nw = normalize_weights(w)
        assert abs(sum(nw.values()) - 1.0) < 1e-9

    def test_equal_weights(self):
        w = {"a": 5, "b": 5, "c": 5}
        nw = normalize_weights(w)
        for v in nw.values():
            assert abs(v - 1/3) < 1e-9

    def test_zero_total(self):
        w = {"a": 0, "b": 0}
        nw = normalize_weights(w)
        assert nw == {"a": 0, "b": 0}


# ─── score_tool ──────────────────────────────────────────────────────────────

class TestScoreTool:
    def test_basic(self):
        scores = {"a": 3, "b": 5}
        weights = {"a": 0.5, "b": 0.5}
        result = score_tool(scores, weights)
        assert abs(result - 4.0) < 1e-9

    def test_missing_criterion(self):
        scores = {"a": 3}
        weights = {"a": 0.5, "b": 0.5}
        result = score_tool(scores, weights)
        assert abs(result - 1.5) < 1e-9


# ─── rank_tools ──────────────────────────────────────────────────────────────

class TestRankTools:
    def test_basic_ranking(self):
        scores = {
            "alpha": {"x": 5, "y": 1},
            "beta":  {"x": 1, "y": 5},
        }
        weights = {"x": 3, "y": 1}
        ranked = rank_tools(scores, weights)
        assert ranked[0][0] == "alpha"
        assert ranked[1][0] == "beta"

    def test_reversed_weights(self):
        scores = {
            "alpha": {"x": 5, "y": 1},
            "beta":  {"x": 1, "y": 5},
        }
        weights = {"x": 1, "y": 3}
        ranked = rank_tools(scores, weights)
        assert ranked[0][0] == "beta"
        assert ranked[1][0] == "alpha"

    def test_equal_scores(self):
        scores = {
            "alpha": {"x": 3, "y": 3},
            "beta":  {"x": 3, "y": 3},
        }
        weights = {"x": 1, "y": 1}
        ranked = rank_tools(scores, weights)
        assert abs(ranked[0][1] - ranked[1][1]) < 1e-9


# ─── analyze_sensitivity ────────────────────────────────────────────────────

class TestSensitivity:
    def test_boost_changes_winner(self):
        scores = {
            "alpha": {"x": 5, "y": 1},
            "beta":  {"x": 1, "y": 5},
        }
        weights = {"x": 3, "y": 3}
        result = analyze_sensitivity(scores, weights, ["x", "y"])

        # Boosting x should favor alpha
        assert result["x"][0][0] == "alpha"
        # Boosting y should favor beta
        assert result["y"][0][0] == "beta"

    def test_returns_full_ranking(self):
        scores = {
            "a": {"x": 5, "y": 1},
            "b": {"x": 3, "y": 3},
            "c": {"x": 1, "y": 5},
        }
        weights = {"x": 1, "y": 1}
        result = analyze_sensitivity(scores, weights, ["x"])
        assert len(result["x"]) == 3


# ─── detect_flips ───────────────────────────────────────────────────────────

class TestDetectFlips:
    def test_flip_detected(self):
        base = [("alpha", 4.0), ("beta", 3.0)]
        sensitivity = {"y": [("beta", 4.5), ("alpha", 3.5)]}
        cnames = {"y": "Criterion Y"}
        flips = detect_flips(base, sensitivity, cnames)
        assert len(flips) == 1
        assert flips[0] == ("Criterion Y", "beta")

    def test_no_flip(self):
        base = [("alpha", 4.0), ("beta", 3.0)]
        sensitivity = {"x": [("alpha", 4.5), ("beta", 3.0)]}
        cnames = {"x": "Criterion X"}
        flips = detect_flips(base, sensitivity, cnames)
        assert len(flips) == 0


# ─── validate_inputs ────────────────────────────────────────────────────────

class TestValidateInputs:
    def test_valid_inputs(self):
        ids = ["x", "y"]
        scores = {"tool": {"x": 3, "y": 4}}
        weights = {"x": 1, "y": 2}
        warnings = validate_inputs(ids, scores, weights)
        assert warnings == []

    def test_missing_rating(self):
        ids = ["x", "y"]
        scores = {"tool": {"x": 3}}
        weights = {"x": 1, "y": 2}
        warnings = validate_inputs(ids, scores, weights)
        assert any("missing rating" in w for w in warnings)

    def test_out_of_range(self):
        ids = ["x"]
        scores = {"tool": {"x": 7}}
        weights = {"x": 1}
        warnings = validate_inputs(ids, scores, weights)
        assert any("outside 1-5" in w for w in warnings)

    def test_invalid_weight_key(self):
        ids = ["x"]
        scores = {"tool": {"x": 3}}
        weights = {"x": 1, "z": 2}
        warnings = validate_inputs(ids, scores, weights)
        assert any("does not match" in w for w in warnings)


# ─── Export Formats ──────────────────────────────────────────────────────────

class TestExportFormats:
    @pytest.fixture
    def sample_data(self):
        criteria_def = [{"id": "x", "name": "Speed"}, {"id": "y", "name": "Quality"}]
        scores = {"alpha": {"x": 5, "y": 3}, "beta": {"x": 3, "y": 5}}
        weights = {"x": 2, "y": 3}
        ranked = rank_tools(scores, weights)
        sensitivity = analyze_sensitivity(scores, weights, ["x", "y"])
        return criteria_def, scores, weights, ranked, sensitivity

    def test_markdown_output(self, sample_data):
        criteria_def, scores, weights, ranked, sensitivity = sample_data
        md = format_markdown(criteria_def, scores, weights, ranked, sensitivity)
        assert "# Product Evaluation Report" in md
        assert "Weighted Ranking" in md
        assert "Sensitivity Analysis" in md

    def test_csv_output(self, sample_data):
        criteria_def, scores, weights, ranked, _ = sample_data
        csv_out = format_csv(criteria_def, scores, weights, ranked)
        assert "Product" in csv_out
        assert "Weighted Score" in csv_out
        assert "alpha" in csv_out or "beta" in csv_out

    def test_terminal_output(self, sample_data):
        criteria_def, scores, weights, ranked, sensitivity = sample_data
        out = format_terminal(criteria_def, scores, weights, ranked, sensitivity)
        assert "PRODUCT EVALUATION RESULTS" in out
        assert "SENSITIVITY ANALYSIS" in out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
