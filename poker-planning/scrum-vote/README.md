# Scrum Vote Anonyme

Mini application web pour voter en mode Scrum Poker avec reveal et reset.

## Lancer

```bash
cd /Users/predictice/workspace/Doctrine/doctrine-tech-day/2026-02/scrum-vote
python3 server.py
```

Puis ouvrir: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Fonctionnalites

- Saisie d'un prenom obligatoire + inscription a la session
- Liste des participants avec statut `a vote` / `pas encore vote`
- Vote sur des cartes Scrum (`0, 1, 2, 3, 5, 8, 13, 21, ?`)
- Reveal automatique des que tous les participants presents ont vote
- `Reveal le vote` pour afficher uniquement les cartes qui ont au moins un vote
- Calcul de la moyenne (en ignorant `?`)
- `Reset le vote en cours` pour remettre a zero
- Anonymat: le reveal affiche uniquement des comptes par carte, jamais les prenoms
