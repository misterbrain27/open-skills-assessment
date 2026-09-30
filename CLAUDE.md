# CLAUDE.md 

Guide de référence rapide pour Claude Code sur ce projet.
Pour les guidelines complètes, voir [AGENTS.md](AGENTS.md).

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Django 5.2 + Django Rest Framework |
| Frontend | Angular 21 (Signals, Standalone, httpResource) |
| Base de données | PostgreSQL |
| Tâches async | Celery + Celery beat, Redis comme broker (à partir de M3) |
| Dépendances Python | uv (Python 3.12) |
| Tests E2E | Playwright |
| Infra | Docker Compose (base + override) |

Plans de référence : [phase 1 (socle commun)](plan-phase1-socle-commun.md),
[phase 2 (test de compétences)](plan-phase2-test-competences.md),
[audit de l'ancienne version](docs/audit-appskills2026.md).

---

## Méthode de travail (apprentissage)

David écrit le code. Pour chaque étape, Claude explique le concept, donne un énoncé avec des
critères d'acceptation, relit le code (ruff + pytest), pose des questions de compréhension et
tient les notes dans `docs/concepts/<milestone>.md` (publiées ensuite sur Notion).
**Claude n'écrit pas le code applicatif à la place de David**, sauf demande explicite.

---

## Commandes essentielles

Le Makefile est construit pendant M1 (étape 8). Cibles prévues :

```bash
make up        # Démarrer la stack Docker
make down      # Arrêter
make test      # pytest
make lint      # ruff check + ruff format --check
make format    # ruff format + ruff check --fix
make migrate   # Appliquer les migrations
make seed      # Données de démo 100 % fictives
make logs      # Logs des conteneurs
```



## Backend (Django / DRF)

- **Modèles** : hériter de `TimeStampedModel` pour `created_at` / `updated_at`
- **ViewSets** : préférer `ModelViewSet` pour le CRUD standard
- **Serializers** : `ModelSerializer` par défaut ; séparer lecture/écriture si nécessaire
- **Documentation** : annoter chaque endpoint avec `@extend_schema` (drf-spectacular)
- **Permissions** : toujours explicite avec `permission_classes`, jamais d'endpoint ouvert sans raison
- **Multi-entreprises** : tout queryset d'API est filtré par l'organisation de l'utilisateur ; un test d'isolation par ressource
- **Logique métier** : dans `services/`, pas dans les vues ni les serializers
- **Migrations** : versionnées, jamais générées au démarrage du conteneur
- **Formatage** : `ruff format` + `ruff check`
- **Tests** : **pytest** + `pytest-django` + `factory_boy`

---

## Frontend (Angular 21)

- **Standalone uniquement** : ne pas mettre `standalone: true` dans le décorateur (c'est le défaut depuis Angular v20+)
- **DI** : `inject()` au lieu du constructeur
- **Réactivité** : Signals (`input()`, `output()`, `computed()`), `@ngrx/signals` pour l'état partagé
- **Data fetching** : `httpResource` dans les services
- **Templates** : `@if`, `@for`, `@switch` — pas de `*ngIf` / `*ngFor`
- **Pas de** `ngClass` / `ngStyle` → utiliser les bindings `class` / `style`
- **Pas de** `@HostBinding` / `@HostListener` → utiliser `host: {}` dans `@Component`
- **ChangeDetection** : `OnPush` systématiquement
- **Images** : `NgOptimizedImage` pour toutes les images statiques
- **Icons** : `lucide-angular` uniquement
- **Accessibilité** : AXE checks + WCAG AA minimum

---

## Règles générales pour Claude

- Lire l'architecture existante avant de proposer une modification
- Ne remplacer qu'une partie d'un fichier si une petite modification suffit
- Ne pas désactiver les vérifications CSRF ou sécurité
- Ne pas supposer un chemin ou une version — vérifier avec les outils disponibles
- Formatage obligatoire avant soumission (ruff côté backend, Prettier côté frontend)
