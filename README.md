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

```bash
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json examples/weights-startup.json
```

Compare different contexts:

```bash
# Startup perspective
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json examples/weights-startup.json

# Enterprise perspective
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json examples/weights-enterprise.json

# Azure-native perspective
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json examples/weights-azure-native.json
```

## How It Works

### 1. Define Criteria

`criteria.json`:
```json
{
  "criteria": [
    {"id": "ux", "name": "Developer Experience"},
    {"id": "docs", "name": "Documentation Quality"},
    {"id": "support", "name": "Enterprise Support"}
  ]
}
```

### 2. Rate Products

`ratings.json`:
```json
{
  "tools": {
    "terraform": {
      "ux": 3,
      "docs": 5,
      "support": 5
    },
    "pulumi": {
      "ux": 5,
      "docs": 4,
      "support": 4
    }
  }
}
```

Ratings are 1-5 scale. Be consistent in what each number means.

### 3. Set Weights

`weights.json`:
```json
{
  "weights": {
    "ux": 5,
    "docs": 3,
    "support": 2
  }
}
```

Higher numbers = more important. Absolute values don't matter (they're normalized), only relative importance.

## Output

The tool shows:

1. **Weighted Ranking** - Final scores based on your weights
2. **Active Weights** - Visual representation of what you prioritized
3. **Tool Profiles** - Top strengths and weaknesses for each option
4. **Sensitivity Analysis** - How rankings change when priorities shift

The sensitivity analysis is the most valuable part. It shows statements like:
- "If you heavily prioritize Developer Experience → Pulumi wins"
- "If you heavily prioritize Industry Adoption → Terraform wins"

This is much more persuasive than "Tool X scored 4.21."

## Use Cases

This tool works for any product selection:
- IaC tools (Terraform, Pulumi, Bicep)
- CI/CD platforms (GitHub Actions, GitLab, Jenkins)
- Monitoring solutions (Datadog, New Relic, Prometheus)
- Cloud providers (AWS, Azure, GCP)
- Databases, message queues, etc.

Just define your criteria, rate the options, and set weights for your context.

## Important Notes

### This is a decision support tool, not a truth machine

The output is only as good as:
- The input scores (who rated them?)
- The criteria definitions (are they clear?)
- The weights (whose priorities?)

### Watch for criteria overlap

These are related and may double-count advantages:
- Documentation
- Community support
- Industry adoption
- Talent availability

Either combine them or be conscious you're weighting ecosystem heavily.

### Avoid false precision

Don't treat 4.21 vs 4.07 as meaningful. The value is in:
- Seeing tradeoffs clearly
- Understanding sensitivity to priorities
- Creating shared language for discussion

## Extending the Tool

To make this more enterprise-grade, consider adding:

- **Multiple personas** - Platform Engineer, Security, Executive views
- **Confidence scores** - How certain are you about each rating?
- **Notes per rating** - Why did you score it this way?
- **Export formats** - Markdown reports, CSV for spreadsheets
- **Decision profiles** - Auto-label results like "best for regulated enterprise"

## Philosophy

There is no universal "best tool," only:

**Best tool for a weighted context.**

- A startup may heavily weight speed, flexibility, developer experience
- A bank may heavily weight policy control, support, auditability, talent
- A cloud-specific team may weight provider-native alignment over portability

This tool makes that context explicit.

## Using This for Other Product Categories

The tool works for any product selection. Here's how to adapt it:

### 1. CI/CD Platform Selection

Create `cicd-criteria.json`:
```json
{
  "criteria": [
    {"id": "ease", "name": "Ease of Setup"},
    {"id": "yaml", "name": "Config Simplicity"},
    {"id": "integrations", "name": "Third-Party Integrations"},
    {"id": "speed", "name": "Build Speed"},
    {"id": "cost", "name": "Cost Efficiency"},
    {"id": "security", "name": "Security Features"}
  ]
}
```

Create `cicd-ratings.json`:
```json
{
  "tools": {
    "github-actions": {
      "ease": 5,
      "yaml": 4,
      "integrations": 5,
      "speed": 4,
      "cost": 4,
      "security": 4
    },
    "gitlab-ci": {
      "ease": 4,
      "yaml": 4,
      "integrations": 4,
      "speed": 4,
      "cost": 5,
      "security": 5
    },
    "jenkins": {
      "ease": 2,
      "yaml": 3,
      "integrations": 5,
      "speed": 3,
      "cost": 5,
      "security": 3
    }
  }
}
```

Create weight profiles for different contexts (startup vs enterprise, cloud-native vs on-prem, etc.).

### 2. Monitoring Solution Selection

```json
{
  "criteria": [
    {"id": "setup", "name": "Setup Time"},
    {"id": "apm", "name": "APM Quality"},
    {"id": "logs", "name": "Log Management"},
    {"id": "alerts", "name": "Alerting"},
    {"id": "cost", "name": "Cost at Scale"},
    {"id": "retention", "name": "Data Retention"}
  ]
}
```

Rate Datadog, New Relic, Prometheus/Grafana, etc.

### 3. Database Selection

```json
{
  "criteria": [
    {"id": "perf", "name": "Query Performance"},
    {"id": "scale", "name": "Horizontal Scalability"},
    {"id": "ops", "name": "Operational Simplicity"},
    {"id": "consistency", "name": "Consistency Model"},
    {"id": "ecosystem", "name": "Ecosystem/Tooling"}
  ]
}
```

### General Pattern

1. **Identify 5-10 criteria** that matter for your category
2. **Rate each option 1-5** on each criterion (be consistent about what each number means)
3. **Create weight profiles** for different organizational contexts
4. **Run comparisons** and use sensitivity analysis to guide discussion

## Adding Features

The tool is intentionally minimal. Here are common extensions:

### 1. Multiple Personas

Add persona-specific weights in one file:

```json
{
  "personas": {
    "developer": {
      "ux": 5,
      "docs": 4,
      "support": 2
    },
    "security": {
      "ux": 2,
      "docs": 3,
      "support": 5,
      "policy": 5
    },
    "executive": {
      "support": 5,
      "adoption": 5,
      "talent": 5
    }
  }
}
```

Modify `evaluate.py` to loop through personas and show how each role would rank the tools.

### 2. Confidence Scores

Add confidence to ratings:

```json
{
  "tools": {
    "terraform": {
      "ux": {"score": 3, "confidence": 5},
      "docs": {"score": 5, "confidence": 5},
      "support": {"score": 5, "confidence": 4}
    }
  }
}
```

Use confidence to flag uncertain ratings or weight them differently.

### 3. Rating Notes

Add justification for each score:

```json
{
  "tools": {
    "terraform": {
      "ux": {
        "score": 3,
        "note": "HCL is declarative but verbose. State management adds complexity."
      }
    }
  }
}
```

Export these to markdown reports for documentation.

### 4. Export Formats

Add functions to `evaluate.py`:

```python
def export_markdown(results):
    # Generate markdown report
    pass

def export_csv(results):
    # Generate CSV for spreadsheet analysis
    pass
```

### 5. Decision Profiles

Auto-label results based on the winner and weight distribution:

```python
def classify_decision(winner, weights):
    if weights['support'] > 0.2 and weights['adoption'] > 0.2:
        return "Best for regulated enterprise"
    elif weights['ux'] > 0.2 and weights['bootstrap'] > 0.2:
        return "Best for fast-moving dev team"
    # etc.
```

### 6. Interactive Mode

Instead of JSON files, prompt for weights:

```python
def interactive_weights(criteria):
    weights = {}
    print("Rate importance of each criterion (1-5):")
    for c in criteria:
        weights[c['id']] = int(input(f"{c['name']}: "))
    return weights
```

### 7. Comparison Mode

Show side-by-side comparison of two weight profiles:

```bash
python evaluate.py examples/iac-criteria.json examples/iac-ratings.json \
  --compare examples/weights-startup.json examples/weights-enterprise.json
```

### 8. Web Interface

Build a simple Flask/FastAPI app that:
- Lets users adjust weights with sliders
- Shows real-time ranking updates
- Exports results as PDF reports

## Implementation Tips

**Keep ratings separate from weights.** Ratings should be relatively objective assessments. Weights encode organizational priorities and context.

**Use 1-5 scale consistently.** Define what each number means upfront:
- 1 = Poor/Missing
- 2 = Below Average
- 3 = Adequate
- 4 = Good
- 5 = Excellent

**Involve multiple stakeholders in rating.** Average scores from platform engineers, security, and leadership to reduce bias.

**Create weight profiles, not individual weights.** Think in terms of "startup context" vs "enterprise context" rather than one-off weight assignments.

**Use sensitivity analysis to drive conversation.** The goal isn't to get a single number. It's to understand: "Under what conditions does each tool win?"

## When This Tool Helps Most

- **Pre-decision alignment** - Before evaluating vendors, agree on criteria and weights
- **Stakeholder disagreement** - Make implicit priorities explicit
- **Audit trail** - Document why a decision was made
- **Re-evaluation** - When context changes (acquisition, new regulations, team growth), re-run with updated weights

## When This Tool Doesn't Help

- **Criteria are unclear** - If you can't define what matters, scoring won't help
- **Missing information** - If you haven't actually tested the tools, ratings are guesses
- **Political decisions** - If the decision is already made, this just creates theater
- **Single criterion dominates** - If one factor is 10x more important than others, you don't need a scoring tool
