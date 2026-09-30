# 0001 — Django + DRF plutôt que FastAPI

- Statut : acceptée
- Date : 2026-09-30

## Contexte

L'application fait passer des tests de compétences : des recruteurs gèrent une banque de
questions, invitent des candidats, et consultent des scores. Elle est multi-entreprises :
chaque organisation ne doit voir que ses propres données.

Le besoin est surtout du CRUD relationnel (organisations, utilisateurs, questions, choix,
tests, invitations, tentatives, réponses), avec des règles d'accès par rôle et par
organisation. Il n'y a ni temps réel ni forte charge attendue.

Deux options ont été envisagées, toutes deux en Python 3.12 :

- **Django 5.2 + Django REST Framework** : framework complet (ORM, migrations, admin,
  authentification, permissions).
- **FastAPI** : framework léger et asynchrone, à assembler avec SQLAlchemy, Alembic et une
  solution d'authentification.

## Décision

Le backend est écrit avec **Django 5.2 et Django REST Framework**.

## Conséquences

Ce que ça apporte :

- **Back-office immédiat** : l'admin Django sert à gérer la banque de questions et les
  organisations sans écrire d'interface dédiée.
- **ORM et migrations intégrés** : le schéma est versionné et relu en PR, sans outil
  supplémentaire à configurer.
- **Multi-entreprises** : le filtrage par organisation se fait dans `get_queryset`, et les
  rôles dans des classes de permission DRF, à un seul endroit par ressource.
- **Moins de code d'assemblage** : modèle utilisateur, hachage des mots de passe, throttling
  et pagination sont fournis et éprouvés.
- **Sécurité** : `manage.py check --deploy` vérifie la configuration de production.

Ce qu'on perd ou ce qu'on accepte :

- **Pas d'asynchrone natif de bout en bout** : DRF est synchrone. Un besoin de temps réel
  (WebSocket, suivi en direct d'une session) demanderait Django Channels ou un service à part.
- **Validation et typage moins stricts** : les serializers DRF sont plus verbeux et moins
  typés que les modèles Pydantic.
- **Documentation OpenAPI non native** : elle dépend de `drf-spectacular` et d'annotations
  `@extend_schema` à maintenir.
- **Framework plus lourd** : démarrage plus lent et plus de conventions implicites à connaître
  qu'avec FastAPI.

Ces limites ne sont pas décisives ici : les traitements longs partiront dans des tâches Celery
(à partir de M3), et la charge attendue ne justifie pas l'asynchrone.
