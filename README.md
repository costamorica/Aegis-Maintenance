# Aegis Maintenance

Orchestrateur de maintenance système pour postes Linux.

## Structure du projet

Cette arborescence initiale suit la proposition d’architecture :

- `bin/aegis-maintenance` : point d’entrée minimal.
- `lib/aegis_maintenance/` : package Python principal.
- `docs/architecture/architecture.md` : document fondateur d’architecture.
- `tests/` : base pour les tests unitaires et d’intégration.

## État actuel

Ce projet est une preuve de concept architecturale pour un outil de maintenance Linux.

- `check` est désormais renforcé et fonctionne sur Gentoo, Arch Linux et EndeavourOS.
- `update` génère maintenant un plan de mise à jour déclaratif et sûr pour EndeavourOS, via un moteur de workflow de planification (`ExecutionPlan` / `UpdatePlanningWorkflow`).
- `clean`, `report` et `doctor` restent des squelettes de commande.
- La sélection de backend rejette désormais les distributions non supportées.

## Installation recommandée

Pour ne pas polluer l’environnement système, utilisez un environnement virtuel :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

L’outil est conçu pour être utilisé depuis un environnement isolé, afin d’éviter de mélanger les dépendances avec celles du système.

## Exécution

```bash
aegis-maintenance check
```

Pour une sortie structurée :

```bash
aegis-maintenance check --format json
```

ou :

```bash
aegis-maintenance check --format markdown
```

Le format `markdown` est utile pour intégrer facilement le rapport dans des notes ou des tickets.

## Limitations

- seul `check` est actuellement supporté pour un usage expérimental.
- `update`, `clean`, `report` et `doctor` sont fournis comme interfaces, pas comme workflows entièrement implémentés.
- sur Gentoo, l’outil utilise la détection de profil Portage via `/etc/portage/make.profile`.

## Documentation

Le document d’architecture est disponible dans `docs/architecture/architecture.md`.
