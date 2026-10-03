# 0003 — Refresh token en cookie HttpOnly, access token en en-tête Bearer

- Statut : acceptée
- Date : 2026-10-02

## Contexte

L'API a un seul client : le front Angular, exécuté dans le navigateur des recruteurs. Les
candidats ne se connectent pas : ils passeront par le lien de leur invitation (M3), en dehors
de cette décision.

L'authentification utilise des JWT (simplejwt) :

- un **access token** de courte durée, présenté à chaque requête ;
- un **refresh token** de plus longue durée, qui sert seulement à obtenir un nouvel access
  token sans redemander le mot de passe.

La question est de savoir **où le navigateur range ces tokens**. Deux attaques sont en jeu :

- **XSS** : un script injecté dans la page lit tout ce qui est accessible en JavaScript
  (`localStorage`, `sessionStorage`, variables) et peut l'envoyer à l'attaquant, qui s'en sert
  ensuite depuis sa propre machine.
- **CSRF** : un autre site fait envoyer à notre API une requête par le navigateur de la
  victime. Le navigateur y joint automatiquement les cookies de notre domaine.

La version précédente du projet stockait le JWT dans un cookie, mais n'appliquait aucune
protection CSRF : DRF ne l'applique qu'avec `SessionAuthentication`, et le login était marqué
`csrf_exempt`. Elle avait donc le risque du cookie sans la protection qui va avec.

Trois options ont été envisagées :

- **Tout en cookie `HttpOnly`, avec protection CSRF** : aucun token n'est lisible par
  JavaScript, mais tous les endpoints deviennent exposés au CSRF. Il faut appliquer la
  protection partout, avec une authentification écrite sur mesure : c'est précisément ce que
  l'ancien projet a raté.
- **En-tête Bearer pur, tokens dans `localStorage`** : pas de CSRF possible, et c'est le plus
  simple. Mais une XSS vole le refresh token et l'utilise depuis une autre machine pendant
  toute sa durée de vie.
- **Hybride** : access token en mémoire et envoyé en en-tête Bearer, refresh token dans un
  cookie `HttpOnly` réservé aux endpoints d'authentification.

## Décision

**Le refresh token vit dans un cookie `HttpOnly`, l'access token en mémoire, envoyé en
en-tête `Authorization: Bearer`.**

- Le login renvoie l'access token dans le corps de la réponse, et le refresh token
  **uniquement** dans un cookie `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/api/auth/`,
  qui expire en même temps que lui.
- Le front garde l'access token en mémoire, jamais dans `localStorage`. Quand il expire, ou
  quand la page est rechargée, le front appelle `/api/auth/refresh/`, qui lit le cookie.
- Durées : 15 minutes pour l'access token, 1 jour pour le refresh token.
- Chaque refresh renvoie un nouveau refresh token (rotation) et met l'ancien sur liste noire.
  Le logout met le refresh token sur liste noire et supprime le cookie.
- Le login n'accepte que du JSON. Un formulaire HTML envoyé depuis un autre site ne peut pas
  produire de JSON, ce qui bloque le *login CSRF* (connecter la victime au compte de
  l'attaquant).

Raison principale : **aucun token de longue durée n'est lisible par JavaScript**, et
l'exposition au CSRF se limite à deux endpoints que `SameSite=Strict` protège.

## Conséquences

Ce que ça apporte :

- **Une XSS ne peut pas emporter le refresh token** : il est illisible par JavaScript.
- **Pas de CSRF sur le reste de l'API** : elle n'accepte que l'en-tête Bearer, qu'un autre
  site ne peut pas faire envoyer par le navigateur.
- **Le refresh token voyage peu** : grâce à `Path=/api/auth/`, il n'accompagne que le refresh
  et le logout, pas chaque requête.
- **La session survit au rechargement de la page**, sans stocker de token dans le navigateur
  en dehors du cookie.

Ce qu'on perd ou ce qu'on accepte :

- **Une XSS reste grave.** Tant que la page est ouverte, le script peut appeler l'API au nom
  de l'utilisateur, lire l'access token en mémoire et en obtenir de nouveaux par
  `/api/auth/refresh/`. Ce qui limite les dégâts : l'access token ne vit que 15 minutes,
  Angular échappe par défaut ce qu'il affiche, et une politique CSP sera posée avec le front.
- **Le logout n'est pas immédiat pour l'access token** : il reste valable jusqu'à son
  expiration, 15 minutes au plus.
- **Contrainte de déploiement** : le front et l'API doivent être sur le même site, par exemple
  le même domaine avec l'API sous `/api` derrière un reverse proxy. Sinon, `SameSite=Strict`
  empêche le navigateur d'envoyer le cookie.
- **Du code en plus** : simplejwt ne gère pas les cookies. Les vues de login, de refresh et de
  logout sont surchargées, et doivent être testées comme le reste.
- **Pas de détection de réutilisation** : simplejwt refuse un refresh token déjà utilisé, mais
  ne révoque pas toute la chaîne de tokens qui en descend. Le cookie `HttpOnly` rend ce vol
  difficile ; la limite est acceptée.

Cette décision sera remplacée par un nouvel ADR si l'un de ces cas se présente :

- un client hors navigateur (application mobile, intégration par API) : il utiliserait le
  Bearer avec un refresh token dans le corps de la réponse ;
- un front servi depuis un autre site que l'API ;
- un besoin de couper immédiatement l'accès d'un compte compromis, qui demanderait un access
  token plus court ou une vérification côté serveur à chaque requête.
