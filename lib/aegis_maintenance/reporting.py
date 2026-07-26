import json
from datetime import datetime
from typing import Any, Dict, List


def render_report(report: Any, fmt: str = "text", verbose: bool = False) -> str:
    report_data = _normalize_report(report)
    if fmt == "json":
        return json.dumps(report_data, indent=2, default=_json_default)
    if fmt == "markdown":
        return _render_markdown(report_data)
    return _render_text(report_data, verbose)


def _normalize_report(report: Any) -> Dict[str, Any]:
    if hasattr(report, "to_dict"):
        return report.to_dict()
    if isinstance(report, dict):
        return report
    return {
        "id": getattr(report, "id", None),
        "timestamp": getattr(report, "timestamp", None),
        "backend": getattr(report, "backend", None),
        "distribution": getattr(report, "distribution", None),
        "command": getattr(report, "command", None),
        "status": getattr(report, "status", None),
        "diagnostics": getattr(report, "diagnostics", []),
        "actions": getattr(report, "actions", []),
        "metadata": getattr(report, "metadata", {}),
    }


def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def _render_text(report: Dict[str, Any], verbose: bool) -> str:
    lines = [
        f"Aegis Maintenance report: {report.get('id')}",
        f"Backend: {report.get('backend')}",
        f"Distribution: {report.get('distribution')}",
        f"Command: {report.get('command')}",
        f"Status: {report.get('status')}",
    ]

    metadata = report.get("metadata", {})
    if metadata:
        lines.append("Metadata:")
        for key, value in metadata.items():
            lines.append(f"  - {key}: {value}")

    if verbose:
        lines.append("Diagnostics:")
        for diagnostic in report.get("diagnostics", []):
            lines.append(_format_diagnostic(diagnostic))
        lines.append("Actions:")
        for action in report.get("actions", []):
            lines.append(f"  - {json.dumps(action)}")
    else:
        levels = _summarize_levels(report.get("diagnostics", []))
        lines.append("Summary:")
        lines.extend([f"  - {level}: {count}" for level, count in levels.items()])

        important = [d for d in report.get("diagnostics", []) if d.get("level") in {"NOTICE", "WARNING", "ERROR", "CRITICAL"}]
        if important:
            lines.append("Important diagnostics:")
            for diagnostic in important:
                lines.append(_format_diagnostic(diagnostic))

    return "\n".join(lines)


def _render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        f"# Aegis Maintenance report: {report.get('id')}",
        "",
        f"- **Backend**: {report.get('backend')}",
        f"- **Distribution**: {report.get('distribution')}",
        f"- **Command**: {report.get('command')}",
        f"- **Status**: {report.get('status')}",
    ]

    metadata = report.get("metadata", {})
    if metadata:
        lines.append("")
        lines.append("## Metadata")
        for key, value in metadata.items():
            lines.append(f"- **{key}**: {value}")

    lines.append("")
    lines.append("## Diagnostics")
    for diagnostic in report.get("diagnostics", []):
        lines.append(f"- **{diagnostic.get('level')}** {diagnostic.get('title')}")
        if diagnostic.get("detail"):
            lines.append(f"  - {diagnostic.get('detail')}")

    lines.append("")
    lines.append("## Actions")
    for action in report.get("actions", []):
        if isinstance(action, dict) and "note" in action:
            lines.append(f"- {action['note']}")
        else:
            lines.append(f"- {json.dumps(action)}")

    return "\n".join(lines)


def _format_diagnostic(diagnostic: Dict[str, Any]) -> str:
    lines = [f"  - [{diagnostic.get('level')}] {diagnostic.get('title')}"]
    if diagnostic.get("detail"):
        lines.append(f"      detail: {diagnostic.get('detail')}")
    if diagnostic.get("data"):
        lines.append(f"      data: {json.dumps(diagnostic.get('data'), indent=2)}")
    return "\n".join(lines)


def _summarize_levels(diagnostics: List[Dict[str, Any]]) -> Dict[str, int]:
    levels = {"OK": 0, "INFO": 0, "NOTICE": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0, "UNKNOWN": 0}
    for diagnostic in diagnostics:
        level = diagnostic.get("level", "UNKNOWN")
        if level in levels:
            levels[level] += 1
        else:
            levels["UNKNOWN"] += 1
    return levels
