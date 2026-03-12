#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def load_json(path):
    with open(path) as f:
        return json.load(f)

def normalize_weights(weights):
    total = sum(weights.values())
    return {k: v/total for k, v in weights.items()}

def score_tool(tool_ratings, weights):
    return sum(tool_ratings.get(c, 0) * w for c, w in weights.items())

def rank_tools(tools, weights):
    norm_weights = normalize_weights(weights)
    scores = {name: score_tool(ratings, norm_weights) for name, ratings in tools.items()}
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def analyze_sensitivity(tools, base_weights, criteria):
    """Show how rankings change when individual criteria are heavily weighted"""
    results = {}
    for crit_id in criteria:
        boosted = {k: (v * 3 if k == crit_id else v) for k, v in base_weights.items()}
        ranked = rank_tools(tools, boosted)
        winner = ranked[0][0]
        results[crit_id] = winner
    return results

def format_output(criteria_def, tools, weights, ranked, sensitivity):
    norm_weights = normalize_weights(weights)
    
    print("\n" + "="*60)
    print("PRODUCT EVALUATION RESULTS")
    print("="*60)
    
    print("\n📊 WEIGHTED RANKING:\n")
    for i, (name, score) in enumerate(ranked, 1):
        print(f"{i}. {name.upper()}: {score:.2f}")
    
    print("\n⚖️  ACTIVE WEIGHTS:\n")
    for crit_id, weight in sorted(norm_weights.items(), key=lambda x: x[1], reverse=True):
        crit_name = next(c['name'] for c in criteria_def if c['id'] == crit_id)
        bar = "█" * int(weight * 50)
        print(f"{crit_name:30} {bar} {weight:.2%}")
    
    print("\n🔍 TOOL PROFILES:\n")
    for name, ratings in tools.items():
        print(f"{name.upper()}:")
        strengths = sorted(ratings.items(), key=lambda x: x[1], reverse=True)[:2]
        weaknesses = sorted(ratings.items(), key=lambda x: x[1])[:2]
        
        for crit_id, score in strengths:
            crit_name = next(c['name'] for c in criteria_def if c['id'] == crit_id)
            print(f"  ✓ {crit_name}: {score}/5")
        
        for crit_id, score in weaknesses:
            crit_name = next(c['name'] for c in criteria_def if c['id'] == crit_id)
            print(f"  ✗ {crit_name}: {score}/5")
        print()
    
    print("🎯 SENSITIVITY ANALYSIS:\n")
    print("If you heavily prioritize...\n")
    for crit_id, winner in sensitivity.items():
        crit_name = next(c['name'] for c in criteria_def if c['id'] == crit_id)
        print(f"  {crit_name:30} → {winner} wins")
    
    print("\n" + "="*60)

def main():
    if len(sys.argv) < 4:
        print("Usage: python evaluate.py <criteria.json> <ratings.json> <weights.json>")
        sys.exit(1)
    
    criteria_def = load_json(sys.argv[1])['criteria']
    tools = load_json(sys.argv[2])['tools']
    weights = load_json(sys.argv[3])['weights']
    
    ranked = rank_tools(tools, weights)
    sensitivity = analyze_sensitivity(tools, weights, weights.keys())
    
    format_output(criteria_def, tools, weights, ranked, sensitivity)

if __name__ == "__main__":
    main()
