# Product Evaluation Tool

A decision clarification tool for enterprise product selection. Forces hidden assumptions about priorities into the open through explicit criteria, ratings, and weights.

## Why This Exists

In enterprise tool selection, arguments happen at the opinion level:
- "Tool X is industry standard"
- "Tool Y is more modern"
- "Tool Z has better support"

The real disagreement is underneath:
- Which criteria matter most?
- How much do they matter?
- Are we optimizing for now or later?

This tool makes those tradeoffs visible and creates a repeatable decision process.

## Quick Start

### CLI

```bash
# Basic evaluation
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json examples/weights-startup.json

# Compare different contexts
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json examples/weights-enterprise.json
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json examples/weights-azure-native.json

# Detailed ratings with confidence scores and notes
python evaluate.py examples/iac-criteria.json examples/iac-ratings-detailed.json examples/weights-startup.json
```

### Web Interface

Open `web/index.html` in any browser — no server required. Features interactive weight sliders, real-time ranking updates, sensitivity heatmap, and export.

## Features

### Core Evaluation
- **Weighted scoring** with normalized weights
- **Sensitivity analysis** showing how rankings change when priorities shift
- **Flip detection** — flags when a priority change causes a different tool to win
- **Tool profiles** — top strengths and weaknesses per product

### Flexible Rating Formats

Plain integers:
```json
{"tools": {"terraform": {"ux": 3, "docs": 5}}}
```

Or with confidence and notes:
```json
{"tools": {"terraform": {"ux": {"score": 3, "confidence": 4, "note": "HCL is verbose"}}}}
```

Mix both formats freely. The engine auto-detects.

### Multi-Persona Mode

Define weights for different stakeholders in one file:

```json
{
  "personas": {
    "Platform Engineer": {"ux": 5, "docs": 3, "support": 3},
    "Security Lead": {"ux": 2, "docs": 3, "support": 5},
    "VP of Infrastructure": {"ux": 2, "docs": 3, "support": 5}
  }
}
```

```bash
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json examples/personas-iac.json --personas
```

### Comparison Mode

Compare two weight profiles side-by-side:

```bash
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json \
  --compare examples/weights-startup.json examples/weights-enterprise.json
```

### Export Formats

```bash
# Markdown report
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json examples/weights-startup.json --export md

# CSV for spreadsheets
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json examples/weights-startup.json --export csv
```

### Web Interface

`web/index.html` — fully client-side, zero dependencies:

- **Dark glassmorphism design** with smooth animations
- **Paste or drag-and-drop JSON** files
- **Interactive weight sliders** — rankings update in real-time
- **Score heatmap** — visual comparison across all criteria
- **Persona tabs** — switch between stakeholder perspectives
- **Export** — download markdown or CSV reports
- **Built-in IaC example** — one click to load and explore

## How It Works

### 1. Define Criteria

```json
{
  "criteria": [
    {"id": "ux", "name": "Developer Experience"},
    {"id": "docs", "name": "Documentation Quality"},
    {"id": "support", "name": "Enterprise Support"}
  ]
}
```

### 2. Rate Products (1-5 scale)

```json
{
  "tools": {
    "terraform": {"ux": 3, "docs": 5, "support": 5},
    "pulumi": {"ux": 5, "docs": 4, "support": 4}
  }
}
```

### 3. Set Weights

```json
{
  "weights": {"ux": 5, "docs": 3, "support": 2}
}
```

Higher numbers = more important. Absolute values don't matter (they're normalized), only relative importance.

## Output

1. **Weighted Ranking** — final scores with proportional bar chart
2. **Active Weights** — visual representation of priorities
3. **Tool Profiles** — top strengths and weaknesses (with notes and confidence if provided)
4. **Sensitivity Analysis** — how rankings change when individual criteria are boosted
5. **Flip Detection** — specifically flags when a priority shift would change the winner

The sensitivity analysis is the most valuable part:
- "If you heavily prioritize Developer Experience → Pulumi wins ⚡ FLIP"
- "If you heavily prioritize Industry Adoption → Terraform wins"

## CLI Reference

```
usage: evaluate.py [-h] [--personas] [--compare W1 W2] [--export {md,csv}]
                   criteria ratings [weights]

positional arguments:
  criteria           Path to criteria JSON file
  ratings            Path to ratings JSON file
  weights            Path to weights JSON file

options:
  --personas         Treat weights file as a persona file
  --compare W1 W2   Compare two weight profile files
  --export {md,csv}  Export format
```

## Example Files

| File | Description |
|------|-------------|
| `examples/iac-criteria.json` | 8 criteria for IaC tool eval |
| `examples/iac-ratings.json` | Plain ratings for 4 IaC tools |
| `examples/iac-ratings-detailed.json` | Same tools with confidence & notes |
| `examples/weights-startup.json` | Startup priorities (UX, speed) |
| `examples/weights-enterprise.json` | Enterprise priorities (support, talent) |
| `examples/weights-azure-native.json` | Azure-focused priorities |
| `examples/personas-iac.json` | 4 stakeholder perspectives |

## Adapting for Other Product Categories

The tool works for any product selection. Just create three JSON files:

1. **Criteria** — what to evaluate (5-10 criteria)
2. **Ratings** — score each product 1-5 on each criterion
3. **Weights** — set importance for your context

Examples: CI/CD platforms, monitoring tools, databases, cloud providers, message queues, etc.

## Important Notes

### This is a decision support tool, not a truth machine

The output is only as good as the input scores, criteria definitions, and weight assignments.

### Watch for criteria overlap

Documentation, community support, adoption, and talent availability are related. Scoring all separately may double-count ecosystem advantages.

### Avoid false precision

Don't treat 4.21 vs 4.07 as meaningful. The value is in seeing tradeoffs clearly, understanding sensitivity, and creating shared language for discussion.

## Testing

```bash
python -m pytest test_evaluate.py -v
```

28 unit tests covering scoring, normalization, sensitivity, validation, and export formats.

## Philosophy

There is no universal "best tool," only:

**Best tool for a weighted context.**

- A startup may heavily weight speed, flexibility, developer experience
- A bank may heavily weight policy control, support, auditability, talent
- A cloud-specific team may weight provider-native alignment over portability

This tool makes that context explicit and the tradeoffs visible.
