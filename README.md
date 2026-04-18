# Moneylook Back

## Authentification

Moneylook ne propose pas d'inscription depuis le front.

Le seul utilisateur autorisé doit être créé ou modifié directement sur le serveur, via les scripts Python du backend. Cela évite d'exposer une route d'inscription publique.

La connexion se fait ensuite depuis le front avec :

- email
- mot de passe

La session expire après 15 minutes sans activité.

## Préparer l'environnement

Depuis le dossier `moneylook-back` :

```bash
source .venv/bin/activate
```

Vérifier que le fichier `.env` contient bien `DATABASE_URL`.

## Créer l'utilisateur admin

À faire une seule fois, sur le serveur :

```bash
python scripts/create_admin_user.py --email admin@example.com
```

Le mot de passe est demandé sans être affiché dans le terminal.

Il est aussi possible de passer le mot de passe en argument, même si ce n'est pas recommandé car il peut rester dans l'historique shell :

```bash
python scripts/create_admin_user.py --email admin@example.com --password "mot-de-passe"
```

Si un utilisateur existe déjà, ce script refuse de créer un second utilisateur.

## Mettre à jour l'utilisateur admin

Pour écraser l'email et le mot de passe de l'utilisateur admin existant :

```bash
python scripts/update_admin_user.py --email nouvel-admin@example.com
```

Le nouveau mot de passe est demandé sans être affiché dans le terminal.

Version avec mot de passe en argument :

```bash
python scripts/update_admin_user.py --email nouvel-admin@example.com --password "nouveau-mot-de-passe"
```

Ce script modifie le premier utilisateur trouvé en base. S'il n'existe aucun utilisateur, il faut d'abord lancer le script de création.
