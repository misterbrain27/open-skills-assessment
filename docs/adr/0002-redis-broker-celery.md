# 0002 — Redis comme broker Celery plutôt que RabbitMQ

- Statut : acceptée
- Date : 2026-09-30

## Contexte

L'application aura des tâches asynchrones à partir de M3 : envoi des invitations par e-mail,
clôture des tentatives dont le délai est dépassé. Celery a besoin d'un broker pour transporter
les messages entre l'API et les workers.

La version précédente du projet utilisait **RabbitMQ comme broker et Redis comme backend de
résultats**, soit deux services avec état à déployer, surveiller et sauvegarder, pour un
volume de quelques tâches par minute.

Deux options ont été envisagées :

- **RabbitMQ + Redis** : un vrai broker de messages (AMQP), et Redis pour les résultats et le
  cache.
- **Redis seul** : broker, backend de résultats et cache dans le même service.

## Décision

**Redis est le seul broker Celery.** RabbitMQ n'est pas déployé.

## Conséquences

Ce que ça apporte :

- **Un service de moins** : la stack Docker se limite à `api`, `db` et `redis`, ce qui
  simplifie le démarrage local, la CI et l'exploitation.
- **Une seule technologie à maîtriser** pour le broker, les résultats et le cache.
- **Suffisant pour le volume attendu** : peu de tâches, courtes, sans routage complexe.

Ce qu'on perd ou ce qu'on accepte :

- **Garanties de livraison plus faibles** : Redis n'est pas un broker AMQP. Il n'a ni
  acquittement au niveau du protocole, ni files durables, ni confirmation de publication. Si
  Redis redémarre sans persistance configurée, les tâches en attente sont perdues.
- **`visibility_timeout`** : une tâche non acquittée dans ce délai (1 heure par défaut) est
  redistribuée à un autre worker. Une tâche longue ou planifiée loin dans le futur
  (`eta`/`countdown`) peut donc être exécutée deux fois.
- **Routage limité** : pas d'exchanges ni de routage par clé ou par motif, et des priorités
  seulement approximatives.

Pour tenir compte de ces limites :

- toutes les tâches sont **idempotentes** : les exécuter deux fois donne le même résultat ;
- les tâches sont déclenchées avec `delay_on_commit`, et jamais planifiées au-delà du
  `visibility_timeout` : les échéances sont traitées par une tâche périodique Celery beat ;
- l'état qui fait foi reste dans PostgreSQL, pas dans le broker.

Si le volume ou le besoin de routage augmente, cette décision sera remplacée par un nouvel ADR.
