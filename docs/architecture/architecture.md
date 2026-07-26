# Architecture Aegis Maintenance

Ce document fondateur expose la vision et l’architecture de Aegis Maintenance.

## Objectif

Aegis Maintenance est un orchestrateur de maintenance système pour postes Linux. Il coordonne les outils natifs des distributions sans les remplacer.

## Architecture modulaire

- `bin/` : point d’entrée minimal.
- `lib/aegis_maintenance/` : code Python principal organisé en couches.
- `lib/aegis_maintenance/backends/` : backends par distribution.
- `lib/aegis_maintenance/detect.py` : détection du système basée sur `/etc/os-release`.
- `lib/aegis_maintenance/reporting.py` : rendu des rapports.
- `tests/` : tests unitaires et de base.

## Roadmap v1.0

- backends Gentoo, Arch, EndeavourOS
- `check`, `update`, `clean`, `report`, `doctor`
- modèles de diagnostic et de rapport
- lecture seule par défaut pour les diagnostics
- journalisation et politique de sécurité
- export JSON et Markdown
