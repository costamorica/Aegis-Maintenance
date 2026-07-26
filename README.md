# Aegis Maintenance

Orchestrateur de maintenance système pour postes Linux.

## Structure du projet

Cette arborescence initiale suit la proposition d’architecture :

- `bin/aegis-maintenance` : point d’entrée minimal.
- `lib/aegis_maintenance/` : package Python principal.
- `docs/architecture/architecture.md` : document fondateur d’architecture.
- `tests/` : base pour les tests unitaires et d’intégration.

## Installation

```bash
python3 -m pip install -e .
```

## Exécution

```bash
python3 -m aegis_maintenance.cli
```

## Documentation

Le document d’architecture est disponible dans `docs/architecture/architecture.md`.
