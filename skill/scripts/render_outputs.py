#!/usr/bin/env python3
"""Render epics.json (produced by the prd-to-jira skill) into Jira-ready artifacts.

Usage:
    python3 render_outputs.py path/to/epics.json --outdir path/to/output

Produces, in --outdir:
    jira_import.csv   - Jira CSV-import-ready epics + stories/tasks
    dependencies.mmd   - Mermaid dependency graph
    dependencies.md    - human-readable dependency list + manual linking steps
    backlog.md          - full backlog as a readable Markdown doc

This script is purely a deterministic renderer. It does not infer epics, tasks,
dependencies, or estimates - that extraction happens upstream, done by the model
following skill/SKILL.md, and is captured in epics.json before this script runs.
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

RISK_CLASS = {"high": "riskHigh", "medium": "riskMedium", "low": "riskLow"}


def load_epics(path: Path) -> dict:
    data = json.loads(path.read_text())
    task_ids = set()
    for epic in data.get("epics", []):
        for task in epic.get("tasks", []):
            task_ids.add(task["id"])

    errors = []
    for epic in data.get("epics", []):
        for task in epic.get("tasks", []):
            for dep in task.get("depends_on", []):
                if dep not in task_ids:
                    errors.append(f"{task['id']} depends_on unknown id '{dep}'")
    if errors:
        raise ValueError(
            "epics.json failed validation:\n  " + "\n  ".join(errors)
        )
    return data


def write_jira_csv(data: dict, outdir: Path) -> None:
    fieldnames = [
        "Issue Type",
        "Summary",
        "Description",
        "Epic Name",
        "Epic Link",
        "Priority",
        "Story Points",
        "Labels",
        "Acceptance Criteria",
        "Internal ID",
    ]
    with (outdir / "jira_import.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for epic in data["epics"]:
            writer.writerow(
                {
                    "Issue Type": "Epic",
                    "Summary": epic["summary"],
                    "Description": epic.get("description", ""),
                    "Epic Name": epic["summary"],
                    "Epic Link": "",
                    "Priority": epic.get("priority", "Medium"),
                    "Story Points": "",
                    "Labels": "",
                    "Acceptance Criteria": "",
                    "Internal ID": epic["id"],
                }
            )
            for task in epic["tasks"]:
                writer.writerow(
                    {
                        "Issue Type": task.get("type", "Story"),
                        "Summary": task["summary"],
                        "Description": task.get("description", ""),
                        "Epic Name": "",
                        "Epic Link": epic["summary"],
                        "Priority": task.get("priority", epic.get("priority", "Medium")),
                        "Story Points": task.get("story_points", ""),
                        "Labels": ";".join(task.get("labels", [])),
                        "Acceptance Criteria": " | ".join(
                            task.get("acceptance_criteria", [])
                        ),
                        "Internal ID": task["id"],
                    }
                )


def write_mermaid(data: dict, outdir: Path) -> None:
    lines = ["graph TD"]
    for epic in data["epics"]:
        lines.append(f'  subgraph {epic["id"]} ["{epic["summary"]}"]')
        for task in epic["tasks"]:
            label = f'{task["id"]}: {task["summary"]} ({task.get("story_points", "?")}pt)'
            label = label.replace('"', "'")
            lines.append(f'    {task["id"]}["{label}"]')
        lines.append("  end")

    for epic in data["epics"]:
        for task in epic["tasks"]:
            for dep in task.get("depends_on", []):
                lines.append(f'  {dep} --> {task["id"]}')

    lines.append("  classDef riskHigh fill:#f8d7da,stroke:#c0392b,color:#611a15;")
    lines.append("  classDef riskMedium fill:#fff3cd,stroke:#b8860b,color:#664d03;")
    lines.append("  classDef riskLow fill:#d4edda,stroke:#2e7d32,color:#1e4620;")
    for epic in data["epics"]:
        for task in epic["tasks"]:
            css_class = RISK_CLASS.get(task.get("risk", "low"), "riskLow")
            lines.append(f'  class {task["id"]} {css_class};')

    (outdir / "dependencies.mmd").write_text("\n".join(lines) + "\n")


def write_dependencies_md(data: dict, outdir: Path) -> None:
    lines = [f'# Dependency Map — {data.get("product", "Untitled")}', ""]
    lines.append(
        "Jira's CSV importer cannot create issue links on first import (ticket keys "
        "don't exist yet). Import `jira_import.csv` first, then use this list to add "
        "'is blocked by' links by matching each Internal ID's Summary to the newly "
        "created Jira issue."
    )
    lines.append("")
    lines.append("| Internal ID | Summary | Depends On | Risk |")
    lines.append("|---|---|---|---|")
    for epic in data["epics"]:
        for task in epic["tasks"]:
            deps = ", ".join(task.get("depends_on", [])) or "—"
            lines.append(
                f'| {task["id"]} | {task["summary"]} | {deps} | {task.get("risk", "low")} |'
            )
    lines.append("")
    (outdir / "dependencies.md").write_text("\n".join(lines) + "\n")


def write_backlog_md(data: dict, outdir: Path) -> None:
    total_points = 0
    total_tasks = 0
    high_risk = []
    points_by_epic = {}

    lines = [f'# Backlog — {data.get("product", "Untitled")}', ""]
    lines.append(f'Source PRD: `{data.get("source_prd", "unknown")}`')
    lines.append("")

    for epic in data["epics"]:
        epic_points = sum(t.get("story_points", 0) for t in epic["tasks"])
        points_by_epic[epic["id"]] = epic_points
        total_points += epic_points
        total_tasks += len(epic["tasks"])
        for t in epic["tasks"]:
            if t.get("risk") == "high":
                high_risk.append(t["id"])

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Epics: {len(data['epics'])}")
    lines.append(f"- Tasks: {total_tasks}")
    lines.append(f"- Total story points: {total_points}")
    lines.append(f"- High-risk tasks: {len(high_risk)} ({', '.join(high_risk) or 'none'})")
    lines.append("")

    for epic in data["epics"]:
        lines.append(f'## {epic["id"]}: {epic["summary"]}')
        lines.append("")
        lines.append(f'*Priority: {epic.get("priority", "Medium")} — {points_by_epic[epic["id"]]} pts*')
        lines.append("")
        lines.append(epic.get("description", ""))
        lines.append("")
        for task in epic["tasks"]:
            lines.append(
                f'### {task["id"]} · {task["summary"]} '
                f'[{task.get("type", "Story")}, {task.get("story_points", "?")} pts, '
                f'{task.get("risk", "low")} risk]'
            )
            lines.append("")
            lines.append(task.get("description", ""))
            lines.append("")
            if task.get("acceptance_criteria"):
                lines.append("**Acceptance criteria:**")
                for ac in task["acceptance_criteria"]:
                    lines.append(f"- {ac}")
                lines.append("")
            deps = task.get("depends_on", [])
            lines.append(f"**Depends on:** {', '.join(deps) if deps else 'none'}")
            labels = task.get("labels", [])
            lines.append(f"**Labels:** {', '.join(labels) if labels else 'none'}")
            lines.append("")

    (outdir / "backlog.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("epics_json", type=Path)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    try:
        data = load_epics(args.epics_json)
    except (ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    write_jira_csv(data, args.outdir)
    write_mermaid(data, args.outdir)
    write_dependencies_md(data, args.outdir)
    write_backlog_md(data, args.outdir)

    total_tasks = sum(len(e["tasks"]) for e in data["epics"])
    print(
        f"Rendered {len(data['epics'])} epics / {total_tasks} tasks to {args.outdir}"
    )


if __name__ == "__main__":
    main()
