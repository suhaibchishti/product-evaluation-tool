#!/usr/bin/env python3
"""
Product Evaluation Tool — Decision Clarification Engine

A reusable, weighted scoring tool that makes product selection tradeoffs visible.
Supports flexible rating formats, persona-based analysis, comparison mode,
sensitivity analysis, and markdown/CSV export.
"""

import argparse
import csv
import io
import json
import sys
from pathlib import Path


# ─── Data Loading ────────────────────────────────────────────────────────────

def load_json(path):
    """Load and return parsed JSON from a file path."""
    with open(path) as f:
        return json.load(f)


def parse_rating(value):
    """
    Accept flexible rating formats:
      - plain int/float:  3
      - dict with score:  {"score": 3, "confidence": 4, "note": "..."}
    Returns (score, confidence, note).
    """
    if isinstance(value, dict):
        return (
            value.get("score", 0),
            value.get("confidence"),
            value.get("note"),
        )
    return (value, None, None)


def normalize_ratings(tools_raw):
    """
    Convert a tools dict (possibly with mixed plain/dict ratings)
    into three parallel dicts: scores, confidences, notes.
    """
    scores = {}
    confidences = {}
    notes = {}
    for tool_name, ratings in tools_raw.items():
        scores[tool_name] = {}
        confidences[tool_name] = {}
        notes[tool_name] = {}
        for crit_id, val in ratings.items():
            s, c, n = parse_rating(val)
            scores[tool_name][crit_id] = s
            confidences[tool_name][crit_id] = c
            notes[tool_name][crit_id] = n
    return scores, confidences, notes


# ─── Validation ──────────────────────────────────────────────────────────────

def validate_inputs(criteria_ids, scores, weights):
    """
    Validate that criteria, ratings, and weights are consistent.
    Returns a list of warning strings (empty if all good).
    """
    warnings = []
    crit_set = set(criteria_ids)

    # Check weights reference valid criteria
    for wk in weights:
        if wk not in crit_set:
            warnings.append(f"Weight '{wk}' does not match any criterion ID")

    # Check each tool has ratings for every criterion
    for tool_name, tool_scores in scores.items():
        for cid in criteria_ids:
            if cid not in tool_scores:
                warnings.append(f"Tool '{tool_name}' is missing rating for criterion '{cid}'")
            else:
                s = tool_scores[cid]
                if not (1 <= s <= 5):
                    warnings.append(f"Tool '{tool_name}' criterion '{cid}' score {s} is outside 1-5 range")

    return warnings


# ─── Scoring ─────────────────────────────────────────────────────────────────

def normalize_weights(weights):
    """Normalize weight values so they sum to 1.0."""
    total = sum(weights.values())
    if total == 0:
        return {k: 0 for k in weights}
    return {k: v / total for k, v in weights.items()}


def score_tool(tool_scores, norm_weights):
    """Compute weighted score for a single tool."""
    return sum(tool_scores.get(c, 0) * w for c, w in norm_weights.items())


def rank_tools(scores, weights):
    """Return list of (tool_name, weighted_score) sorted descending."""
    nw = normalize_weights(weights)
    result = [(name, score_tool(s, nw)) for name, s in scores.items()]
    return sorted(result, key=lambda x: x[1], reverse=True)


# ─── Sensitivity Analysis ───────────────────────────────────────────────────

def analyze_sensitivity(scores, base_weights, criteria_ids):
    """
    For each criterion, boost its weight by 3x and return the full ranking.
    Returns dict: {crit_id: [(tool, score), ...]}.
    """
    results = {}
    for cid in criteria_ids:
        boosted = {k: (v * 3 if k == cid else v) for k, v in base_weights.items()}
        results[cid] = rank_tools(scores, boosted)
    return results


def detect_flips(base_ranking, sensitivity, criteria_names):
    """
    Identify criteria where the winner changes compared to the base ranking.
    Returns list of (criterion_name, new_winner) for flips only.
    """
    base_winner = base_ranking[0][0] if base_ranking else None
    flips = []
    for cid, ranking in sensitivity.items():
        if ranking and ranking[0][0] != base_winner:
            cname = criteria_names.get(cid, cid)
            flips.append((cname, ranking[0][0]))
    return flips


# ─── Formatters ──────────────────────────────────────────────────────────────

def criteria_name_map(criteria_def):
    """Build {id: name} lookup from criteria definitions."""
    return {c["id"]: c["name"] for c in criteria_def}


def format_terminal(criteria_def, scores, weights, ranked, sensitivity,
                    confidences=None, notes=None, label=None):
    """Pretty-print results to the terminal."""
    cnames = criteria_name_map(criteria_def)
    nw = normalize_weights(weights)

    lines = []
    lines.append("")
    lines.append("=" * 64)
    title = "PRODUCT EVALUATION RESULTS"
    if label:
        title += f"  —  {label}"
    lines.append(title)
    lines.append("=" * 64)

    # Weighted ranking
    lines.append("\n📊 WEIGHTED RANKING:\n")
    max_score = ranked[0][1] if ranked else 1
    for i, (name, sc) in enumerate(ranked, 1):
        bar_len = int((sc / max_score) * 30) if max_score else 0
        bar = "█" * bar_len
        lines.append(f"  {i}. {name.upper():20} {sc:.2f}  {bar}")

    # Active weights
    lines.append("\n⚖️  ACTIVE WEIGHTS:\n")
    for cid, w in sorted(nw.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(w * 50)
        lines.append(f"  {cnames.get(cid, cid):30} {bar} {w:.1%}")

    # Tool profiles
    lines.append("\n🔍 TOOL PROFILES:\n")
    for name, tool_scores in scores.items():
        lines.append(f"  {name.upper()}:")
        sorted_scores = sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
        top = sorted_scores[:3]
        bottom = sorted_scores[-2:]

        for cid, s in top:
            marker = "✓"
            extra = ""
            if notes and notes.get(name, {}).get(cid):
                extra = f"  ({notes[name][cid]})"
            if confidences and confidences.get(name, {}).get(cid) is not None:
                conf = confidences[name][cid]
                extra = f"  [confidence: {conf}/5]{extra}"
            lines.append(f"    {marker} {cnames.get(cid, cid)}: {s}/5{extra}")

        for cid, s in bottom:
            if (cid, s) not in top:
                marker = "✗"
                lines.append(f"    {marker} {cnames.get(cid, cid)}: {s}/5")
        lines.append("")

    # Sensitivity
    lines.append("🎯 SENSITIVITY ANALYSIS:\n")
    lines.append("  If you heavily prioritize...\n")
    base_winner = ranked[0][0] if ranked else None
    for cid, s_ranking in sensitivity.items():
        winner = s_ranking[0][0] if s_ranking else "?"
        flip = " ⚡ FLIP" if winner != base_winner else ""
        lines.append(f"    {cnames.get(cid, cid):30} → {winner} wins{flip}")

    # Flips summary
    flips = detect_flips(ranked, sensitivity, cnames)
    if flips:
        lines.append("\n  ⚡ Ranking flips detected:")
        for cname, new_winner in flips:
            lines.append(f"    • Heavily weighting {cname} → {new_winner} overtakes {base_winner}")

    lines.append("\n" + "=" * 64)
    return "\n".join(lines)


def format_markdown(criteria_def, scores, weights, ranked, sensitivity,
                    confidences=None, notes=None, label=None):
    """Generate a full markdown report."""
    cnames = criteria_name_map(criteria_def)
    nw = normalize_weights(weights)

    lines = []
    title = "Product Evaluation Report"
    if label:
        title += f" — {label}"
    lines.append(f"# {title}\n")

    # Ranking table
    lines.append("## Weighted Ranking\n")
    lines.append("| Rank | Product | Score |")
    lines.append("|------|---------|-------|")
    for i, (name, sc) in enumerate(ranked, 1):
        lines.append(f"| {i} | {name} | {sc:.2f} |")
    lines.append("")

    # Weights table
    lines.append("## Active Weights\n")
    lines.append("| Criterion | Weight |")
    lines.append("|-----------|--------|")
    for cid, w in sorted(nw.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {cnames.get(cid, cid)} | {w:.1%} |")
    lines.append("")

    # Detailed scores
    lines.append("## Detailed Scores\n")
    crit_ids = [c["id"] for c in criteria_def]
    header = "| Product | " + " | ".join(cnames.get(c, c) for c in crit_ids) + " |"
    sep = "|---------|" + "|".join("------" for _ in crit_ids) + "|"
    lines.append(header)
    lines.append(sep)
    for tool_name, tool_scores in scores.items():
        row = f"| {tool_name} | " + " | ".join(str(tool_scores.get(c, "-")) for c in crit_ids) + " |"
        lines.append(row)
    lines.append("")

    # Notes (if present)
    if notes:
        has_notes = any(n for tool_notes in notes.values() for n in tool_notes.values() if n)
        if has_notes:
            lines.append("## Rating Notes\n")
            for tool_name, tool_notes in notes.items():
                tool_has = [cid for cid, n in tool_notes.items() if n]
                if tool_has:
                    lines.append(f"### {tool_name}\n")
                    for cid in tool_has:
                        lines.append(f"- **{cnames.get(cid, cid)}** ({scores[tool_name].get(cid, '?')}/5): {tool_notes[cid]}")
                    lines.append("")

    # Sensitivity
    lines.append("## Sensitivity Analysis\n")
    lines.append("| If you heavily prioritize... | Winner |")
    lines.append("|------------------------------|--------|")
    base_winner = ranked[0][0] if ranked else None
    for cid, s_ranking in sensitivity.items():
        winner = s_ranking[0][0] if s_ranking else "?"
        flip = " ⚡" if winner != base_winner else ""
        lines.append(f"| {cnames.get(cid, cid)} | {winner}{flip} |")
    lines.append("")

    flips = detect_flips(ranked, sensitivity, cnames)
    if flips:
        lines.append("> **Key insight:** The ranking is sensitive to priority changes.\n")
        for cname, new_winner in flips:
            lines.append(f"> - Heavily weighting *{cname}* → **{new_winner}** overtakes **{base_winner}**")
        lines.append("")

    lines.append("---\n*Generated by Product Evaluation Tool*\n")
    return "\n".join(lines)


def format_csv(criteria_def, scores, weights, ranked):
    """Generate CSV output."""
    cnames = criteria_name_map(criteria_def)
    crit_ids = [c["id"] for c in criteria_def]
    nw = normalize_weights(weights)

    buf = io.StringIO()
    writer = csv.writer(buf)

    # Header
    writer.writerow(["Product", "Weighted Score"] + [cnames.get(c, c) for c in crit_ids])

    # Data rows sorted by rank
    rank_map = {name: sc for name, sc in ranked}
    for name, sc in ranked:
        row = [name, f"{sc:.2f}"] + [str(scores[name].get(c, "")) for c in crit_ids]
        writer.writerow(row)

    # Weights row
    writer.writerow([])
    writer.writerow(["Weights", ""] + [f"{nw.get(c, 0):.1%}" for c in crit_ids])

    return buf.getvalue()


# ─── Persona Support ────────────────────────────────────────────────────────

def run_personas(criteria_def, scores, personas, confidences=None, notes=None,
                 export=None):
    """Run evaluation for each persona and display/export results."""
    outputs = []
    for persona_name, p_weights in personas.items():
        ranked = rank_tools(scores, p_weights)
        crit_ids = list(p_weights.keys())
        sensitivity = analyze_sensitivity(scores, p_weights, crit_ids)

        if export == "md":
            outputs.append(format_markdown(
                criteria_def, scores, p_weights, ranked, sensitivity,
                confidences, notes, label=persona_name
            ))
        elif export == "csv":
            outputs.append(f"# Persona: {persona_name}\n")
            outputs.append(format_csv(criteria_def, scores, p_weights, ranked))
        else:
            outputs.append(format_terminal(
                criteria_def, scores, p_weights, ranked, sensitivity,
                confidences, notes, label=persona_name
            ))
    return "\n".join(outputs)


# ─── Comparison Mode ────────────────────────────────────────────────────────

def run_comparison(criteria_def, scores, weights_a, weights_b, label_a, label_b,
                   confidences=None, notes=None, export=None):
    """Side-by-side comparison of two weight profiles."""
    ranked_a = rank_tools(scores, weights_a)
    ranked_b = rank_tools(scores, weights_b)
    sens_a = analyze_sensitivity(scores, weights_a, list(weights_a.keys()))
    sens_b = analyze_sensitivity(scores, weights_b, list(weights_b.keys()))

    if export == "md":
        out_a = format_markdown(criteria_def, scores, weights_a, ranked_a, sens_a,
                                confidences, notes, label=label_a)
        out_b = format_markdown(criteria_def, scores, weights_b, ranked_b, sens_b,
                                confidences, notes, label=label_b)
    elif export == "csv":
        out_a = f"# Profile: {label_a}\n" + format_csv(criteria_def, scores, weights_a, ranked_a)
        out_b = f"# Profile: {label_b}\n" + format_csv(criteria_def, scores, weights_b, ranked_b)
    else:
        out_a = format_terminal(criteria_def, scores, weights_a, ranked_a, sens_a,
                                confidences, notes, label=label_a)
        out_b = format_terminal(criteria_def, scores, weights_b, ranked_b, sens_b,
                                confidences, notes, label=label_b)

    return out_a + "\n" + out_b


# ─── CLI ─────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        description="Product Evaluation Tool — Decision Clarification Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s criteria.json ratings.json weights.json
  %(prog)s criteria.json ratings.json weights.json --export md
  %(prog)s criteria.json ratings.json weights.json --export csv
  %(prog)s criteria.json ratings.json personas.json --personas
  %(prog)s criteria.json ratings.json --compare startup.json enterprise.json
        """,
    )
    parser.add_argument("criteria", help="Path to criteria JSON file")
    parser.add_argument("ratings", help="Path to ratings JSON file")
    parser.add_argument("weights", nargs="?", help="Path to weights JSON file")
    parser.add_argument("--personas", action="store_true",
                        help="Treat weights file as a persona file with multiple weight profiles")
    parser.add_argument("--compare", nargs=2, metavar=("W1", "W2"),
                        help="Compare two weight profile files side-by-side")
    parser.add_argument("--export", choices=["md", "csv"],
                        help="Export format: md (markdown) or csv")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Load data
    criteria_def = load_json(args.criteria)["criteria"]
    criteria_ids = [c["id"] for c in criteria_def]
    tools_raw = load_json(args.ratings)["tools"]
    scores, confidences, notes = normalize_ratings(tools_raw)

    # Comparison mode
    if args.compare:
        w1 = load_json(args.compare[0])["weights"]
        w2 = load_json(args.compare[1])["weights"]
        label_a = Path(args.compare[0]).stem
        label_b = Path(args.compare[1]).stem
        output = run_comparison(criteria_def, scores, w1, w2, label_a, label_b,
                                confidences, notes, args.export)
        print(output)
        return

    # Need a weights file for standard and persona modes
    if not args.weights:
        parser.error("weights file is required (unless using --compare)")

    weights_data = load_json(args.weights)

    # Persona mode
    if args.personas:
        if "personas" not in weights_data:
            print("Error: --personas flag used but file does not contain 'personas' key",
                  file=sys.stderr)
            sys.exit(1)
        output = run_personas(criteria_def, scores, weights_data["personas"],
                              confidences, notes, args.export)
        print(output)
        return

    # Standard mode
    weights = weights_data["weights"]

    # Validate
    warnings = validate_inputs(criteria_ids, scores, weights)
    if warnings:
        print("⚠️  Validation warnings:", file=sys.stderr)
        for w in warnings:
            print(f"   • {w}", file=sys.stderr)
        print(file=sys.stderr)

    ranked = rank_tools(scores, weights)
    sensitivity = analyze_sensitivity(scores, weights, criteria_ids)

    if args.export == "md":
        print(format_markdown(criteria_def, scores, weights, ranked, sensitivity,
                              confidences, notes))
    elif args.export == "csv":
        print(format_csv(criteria_def, scores, weights, ranked))
    else:
        print(format_terminal(criteria_def, scores, weights, ranked, sensitivity,
                              confidences, notes))


if __name__ == "__main__":
    main()
