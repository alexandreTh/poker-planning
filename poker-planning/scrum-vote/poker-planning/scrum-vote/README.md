# Scrum Vote Anonyme

Mini application web pour voter en mode Scrum Poker avec reveal et reset.

## Lancer

```bash
cd /Users/predictice/workspace/Doctrine/poker-planning
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scrum-vote/server.py
```

Puis ouvrir: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Deploy sur Vercel

Prerequis:

- Node.js installe
- Compte Vercel

Depuis la racine du repo:

```bash
npm i -g vercel
vercel login
vercel
```

Pour un deploy production:

```bash
vercel --prod
```

Config incluse:

- `vercel.json` route tout le trafic vers `scrum-vote/server.py`
- `requirements.txt` installe Flask pour le runtime Python Vercel

Important:

- L'etat (participants/votes) est en memoire.
- Sur Vercel, cet etat peut etre perdu entre invocations/redeploys.
- Pour un usage equipe fiable, il faut persister l'etat (ex: Vercel KV/Redis).

## Fonctionnalites

- Saisie d'un prenom obligatoire + inscription a la session
- Liste des participants avec statut `a vote` / `pas encore vote`
- Vote sur des cartes Scrum (`0, 1, 2, 3, 5, 8, 13, 21, ?`)
- Reveal automatique des que tous les participants presents ont vote
- `Reveal le vote` pour afficher uniquement les cartes qui ont au moins un vote
- Calcul de la moyenne (en ignorant `?`)
- `Reset le vote en cours` pour remettre a zero
- Anonymat: le reveal affiche uniquement des comptes par carte, jamais les prenoms
