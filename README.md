# Moneylook Back

Backend FastAPI de Moneylook.

Il expose l'API utilisée par le front, gère l'authentification par cookie de session, les données financières, les statistiques et les migrations légères exécutées au démarrage.

## Prérequis serveur

Sur un VPS Linux, prévoir :

- Python 3.12 ou plus récent
- PostgreSQL
- Nginx, recommandé en reverse proxy
- un utilisateur système dédié, par exemple `moneylook`
- un domaine ou sous-domaine pointant vers le VPS

Exemple Debian/Ubuntu :

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip postgresql postgresql-contrib nginx
```

## Installation sur un VPS

Créer un utilisateur système dédié :

```bash
sudo adduser --system --group --home /opt/moneylook moneylook
```

Copier le backend dans `/opt/moneylook/moneylook-back`, puis installer les dépendances :

```bash
cd /opt/moneylook/moneylook-back
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Base PostgreSQL

Créer une base et un utilisateur PostgreSQL :

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE moneylook;
CREATE USER moneylook WITH PASSWORD 'remplacer-par-un-mot-de-passe-fort';
GRANT ALL PRIVILEGES ON DATABASE moneylook TO moneylook;
\c moneylook
GRANT ALL ON SCHEMA public TO moneylook;
\q
```

L'application crée les tables au démarrage avec SQLAlchemy. Elle applique aussi certaines adaptations de schéma déjà prévues dans `main.py`.

## Fichier `.env`

Créer `/opt/moneylook/moneylook-back/.env` :

```env
DATABASE_URL=postgresql+psycopg://moneylook:remplacer-par-un-mot-de-passe-fort@localhost:5432/moneylook
CSRF_TRUSTED_ORIGINS=https://moneylook.example.com
LOGIN_BRUTE_FORCE_ENABLED=true
SESSION_COOKIE_SECURE=true
```

Variables disponibles :

- `DATABASE_URL` : URL SQLAlchemy de la base PostgreSQL. Obligatoire.
- `CSRF_TRUSTED_ORIGINS` : origines autorisées pour les requêtes d'écriture. Mettre l'URL publique du front. Plusieurs valeurs possibles séparées par des virgules.
- `LOGIN_BRUTE_FORCE_ENABLED` : active ou désactive la protection anti brute force du login. En production, garder `true`.
- `SESSION_COOKIE_SECURE` : force l'envoi du cookie de session uniquement en HTTPS. En production, garder `true`.

En local, on peut utiliser :

```env
DATABASE_URL=postgresql+psycopg://moneylook:mot-de-passe@localhost:5432/moneylook
CSRF_TRUSTED_ORIGINS=http://localhost:5173
LOGIN_BRUTE_FORCE_ENABLED=false
SESSION_COOKIE_SECURE=false
```

## Premier démarrage

Depuis le dossier backend :

```bash
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000
```

Tester :

```bash
curl http://127.0.0.1:8000/
```

La réponse attendue est :

```json
{"status":"ok"}
```

## Créer l'utilisateur admin

Moneylook ne propose pas d'inscription depuis le front.

Le seul utilisateur autorisé doit être créé ou modifié directement sur le serveur via les scripts Python du backend. Cela évite d'exposer une route d'inscription publique.

Créer l'admin :

```bash
cd /opt/moneylook/moneylook-back
source .venv/bin/activate
python scripts/create_admin_user.py --email admin@example.com
```

Le mot de passe est demandé sans être affiché dans le terminal.

Si un utilisateur existe déjà, ce script refuse de créer un second utilisateur.

## Mettre à jour l'utilisateur admin

Pour modifier l'email et le mot de passe de l'utilisateur admin existant :

```bash
cd /opt/moneylook/moneylook-back
source .venv/bin/activate
python scripts/update_admin_user.py --email nouvel-admin@example.com
```

Le nouveau mot de passe est demandé sans être affiché dans le terminal.

## Service systemd

Créer `/etc/systemd/system/moneylook-back.service` :

```ini
[Unit]
Description=Moneylook backend
After=network.target postgresql.service

[Service]
User=moneylook
Group=moneylook
WorkingDirectory=/opt/moneylook/moneylook-back
EnvironmentFile=/opt/moneylook/moneylook-back/.env
ExecStart=/opt/moneylook/moneylook-back/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Activer le service :

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now moneylook-back
sudo systemctl status moneylook-back
```

Lire les logs :

```bash
journalctl -u moneylook-back -f
```

## Reverse proxy Nginx

Configuration recommandée : servir le front et l'API sur la même origine HTTPS. Cela simplifie les cookies de session, évite les soucis CORS, et permet de laisser `VITE_API_URL` vide côté front.

Exemple de bloc Nginx :

```nginx
server {
    listen 80;
    server_name moneylook.example.com;

    root /var/www/moneylook;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~ ^/(auth|account-types|bank-accounts|categories|expenses|incomes|recurring-expenses|recurring-incomes|stats)(/|$) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ensuite, ajouter HTTPS avec Certbot ou votre outil habituel, puis vérifier que `SESSION_COOKIE_SECURE=true`.

## Déploiement d'une nouvelle version

```bash
cd /opt/moneylook/moneylook-back
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart moneylook-back
```

Vérifier ensuite :

```bash
systemctl status moneylook-back
curl http://127.0.0.1:8000/
```

## Sécurité

Points importants en production :

- utiliser HTTPS
- garder `SESSION_COOKIE_SECURE=true`
- garder `LOGIN_BRUTE_FORCE_ENABLED=true`
- définir `CSRF_TRUSTED_ORIGINS` avec l'URL publique exacte du front
- protéger le fichier `.env` :

```bash
chmod 600 /opt/moneylook/moneylook-back/.env
chown moneylook:moneylook /opt/moneylook/moneylook-back/.env
```

- sauvegarder régulièrement la base PostgreSQL

Exemple de sauvegarde :

```bash
pg_dump moneylook > moneylook-$(date +%F).sql
```
