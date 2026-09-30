# AI Coding Guidelines 

Ce document définit les standards et les meilleures pratiques pour les modèles IA intervenant sur le projet. Respectez scrupuleusement ces consignes pour garantir la cohérence et la qualité du code.

## 🌟 Principes Généraux
- **Qualité avant tout** : Produisez un code propre, testé et documenté.
- **Cohérence** : Suivez les motifs de conception existants.
- **Explications** : Commentez vos choix techniques complexes.
- **Formatage** : Le code doit être formaté selon les standards du projet (Ruff pour Python, Prettier/Angular pour TypeScript).

---

## 🐍 Backend (Django 5.2 + DRF)

### 1. Code Style
- **Python 3.12** : Utilisez les fonctionnalités modernes de Python (Type Hints, f-strings).
- **Formatage** : Utilisez `ruff format` et `ruff check` (pas de black).
- **Importations** : Regroupez les imports (standard library, third-party, local) et triez-les par ordre alphabétique.


### 2. Modèles (Django)
- **Héritage** : Utilisez `TimeStampedModel` pour les nouveaux modèles afin d'avoir `created_at` et `updated_at` par défaut.
- **Validations** : Gérez les validations au niveau du modèle via `clean()` ou `validators` quand c'est possible.
- **Migrations** : Donnez des noms descriptifs aux migrations si possible.

### 3. API (Django Rest Framework)
- **ViewSets** : Privilégiez les `ModelViewSet` pour les opérations CRUD standards.
- **Serializers** : 
    - Utilisez des `ModelSerializer` par défaut.
    - Séparez les serializers de lecture et d'écriture si nécessaire.
    - Validez les données complexes dans `validate()`.
- **Documentation (OpenAPI)** : Swagger(theme sombre) y compris les exemples de requêtes/réponses.
- **Permissions** : Soyez explicite avec `permission_classes`. Ne laissez jamais un endpoint ouvert sans raison.

### 4. Tâches asynchrones (Celery)
- Utilisez Celery pour les traitements longs (envois de mails, traitement d'images).
- Stockez les tâches dans le `tasks.py` de l'app concernée ; broker Redis.
- Déclenchez-les avec `delay_on_commit` et rendez-les idempotentes.

---

## 🅰️ Frontend (Angular 21)

### 1. Architecture & Composants
- **Standalone Components** : Tous les nouveaux composants doivent être `standalone: true`.
- **Injection de dépendances** : Utilisez la fonction `inject()` au lieu du constructeur.
- **Control Flow** : Utilisez la nouvelle syntaxe `@if`, `@for`, `@switch`.

### 2. Réactivité (SIGNALS)
- **Signals obligatoires** : Utilisez les Signals pour toute la gestion d'état locale et partagée.
- **Data Fetching** : Utilisez `httpResource` (Angular 21) pour les appels API dans les services.
- **Input/Output** : Utilisez la syntaxe `input()`, `output()`, et `model()`.

### 3. Services & API
- **Organisation** : Regroupez les services dans `features/services/`.
- **HttpClient** : Les appels API complexes doivent rester dans les services, les composants ne font qu'appeler ces services et consommer les signals.

### 4. UI & Styles
- **Angular Material** : Utilisez les composants fournis par Material pour une UI cohérente.
- **Icons** : Utilisez uniquement `lucide-angular`.
- **SCSS/CSS** : Respectez le thème global défini dans `material-theme.scss`. Utilisez des variables CSS/SCSS pour les couleurs et espacements.

---

## 🧪 Tests & Validation
- **Backend** : Écrivez des tests unitaires et d'intégration avec **pytest** (`pytest-django`, `factory_boy`).
- **Frontend** : Utilisez Playwright pour les tests E2E.
- **Validation** : Avant de soumettre, vérifiez les erreurs de syntaxe et le linter.

---

## 🤖 Instructions Mode IA
- **Analyse du contexte** : Lisez toujours l'architecture existante avant de proposer une modification.
- **Édition de fichiers** : Ne remplacez pas tout un fichier si une petite modification suffit.
- **Pas de suppositions** : Si un chemin ou une version est incertaine, utilisez les outils de recherche.
- **Sécurité** : Ne proposez jamais de désactiver des CSRF ou des vérifications de sécurité fondamentales.
