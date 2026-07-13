#  Currency Converter

![CI](https://github.com/Fred0242/currency-converter/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.x-green?logo=django)
![Docker](https://img.shields.io/badge/Docker-✓-blue?logo=docker)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)
![Azure Functions](https://img.shields.io/badge/Azure-Functions-0078D4?logo=azurefunctions)
![Render](https://img.shields.io/badge/Deployed%20on-Render-purple?logo=render)

> 🇫🇷 Français | 🇮🇹 [Italiano](#-convertitore-di-valute)

---

## 🇫🇷 Convertisseur de Devises

Application web de conversion de devises en temps réel, développée avec Python/Django et déployée en production sur Render.

###  Lancer le projet (Docker)

```bash
git clone git@github.com:Fred0242/currency-converter.git
cd currency-converter
cp .env.example .env
# Remplis les variables dans .env
docker compose up --build
# Accède à l'app sur http://127.0.0.1:8000
```

---

###  Fonctionnalités

-  Conversion en temps réel via l'API [Frankfurter](https://www.frankfurter.app/)
-  Drapeaux des pays pour chaque devise
-  Devises supportées : EUR, USD, GBP, JPY, CHF, CAD, AUD, XAF (Franc CFA)
-  Authentification (inscription, connexion, déconnexion)
-  Historique personnel des conversions (utilisateurs connectés)
-  Frontend en `fetch()` (HTTP trigger) : le formulaire écrit/lit les données via des appels HTTP JSON, sans rechargement de page
-  Historique des conversions persisté dans **Azure Table Storage**, via une **Azure Function** (HTTP trigger)
-  Interface responsive et moderne

---

###  Stack technique

| Technologie | Rôle |
|---|---|
| Python 3.13 | Langage principal |
| Django 5.x | Framework web |
| PostgreSQL 16 | Base de données (comptes, historique local) |
| Azure Functions (Python) | API HTTP trigger (écriture/lecture des conversions) |
| Azure Table Storage | Persistance de l'historique côté Azure |
| Docker + Compose | Conteneurisation |
| GitHub Actions | CI/CD |
| Render | Déploiement production |
| Gunicorn | Serveur WSGI production |
| Whitenoise | Fichiers statiques |

---

###  Architecture du projet

```
currency_converter/
│
├── core/                   ← Configuration Django
│   ├── settings.py         ← AZURE_FUNCTION_BASE_URL, DB, etc.
│   ├── urls.py
│   └── wsgi.py
│
├── converter/              ← App principale
│   ├── models.py           ← Modèle ConversionHistory
│   ├── views.py            ← Logique de conversion + API JSON (convert_api, history_api)
│   ├── services.py         ← Appel API Frankfurter
│   ├── urls.py              ← Routes /api/convert/ et /api/history/
│   ├── templates/           ← Frontend en fetch() (HTTP trigger)
│   └── tests.py
│
├── users/                  ← App authentification
│   ├── views.py
│   ├── urls.py
│   └── templates/
│
├── azure_function/          ← Azure Function (Python, HTTP trigger)
│   ├── function_app.py     ← Endpoints convert (POST) et history (GET)
│   ├── requirements.txt
│   └── host.json
│
├── .github/workflows/      ← CI/CD GitHub Actions
│   └── ci.yml
│
├── Dockerfile              ← Image Docker
├── docker-compose.yml      ← Orchestration locale
├── railway.toml            ← Configuration Render
└── requirements.txt        ← Dépendances Python
```

---

###  Installation locale (via Docker)

#### Prérequis
- Docker Desktop
- Git

#### Étapes

```bash
# 1. Clone le repo
git clone git@github.com:Fred0242/currency-converter.git
cd currency-converter

# 2. Crée le fichier .env
cp .env.example .env
# Remplis les variables dans .env

# 3. Lance l'app
docker compose up --build

# 4. Accède à l'app
# http://127.0.0.1:8000
```

---

###  API HTTP (écriture / lecture)

Le formulaire de conversion n'envoie plus un POST classique en rechargement de page : le frontend fait des appels `fetch()` en JSON vers une API HTTP.

| Endpoint | Méthode | Rôle |
|---|---|---|
| `/api/convert/` (Django) | POST | Calcule et écrit une conversion (historique sauvegardé si connecté) |
| `/api/history/` (Django) | GET | Lit l'historique de l'utilisateur connecté |
| `{AZURE_FUNCTION_BASE_URL}/api/convert` | POST | Même logique, exécutée par une **Azure Function** (HTTP trigger) |
| `{AZURE_FUNCTION_BASE_URL}/api/history/{username}` | GET | Lit l'historique depuis **Azure Table Storage** |

Le frontend bascule automatiquement vers l'Azure Function si la variable d'environnement `AZURE_FUNCTION_BASE_URL` est définie (voir `.env.example`) ; sinon il retombe sur l'API Django locale (utile en offline / sans compte Azure).

---

###  Azure Function (HTTP trigger + Table Storage)

Le dossier [`azure_function/`](azure_function/) contient une Azure Function Python (modèle v2) avec deux endpoints HTTP trigger qui écrivent/lisent l'historique des conversions dans une table Azure (`ConversionHistory`), indépendamment de la base PostgreSQL.

**Ressources Azure utilisées** : un Resource Group, un Storage Account (Table Storage) et une Function App (plan Consumption, Python 3.12, Linux).

**Déploiement** (nécessite [Azure CLI](https://learn.microsoft.com/cli/azure/) et les [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)) :

```bash
# 1. Connexion
az login

# 2. Création des ressources (une seule fois)
az group create --name rg-currency-converter --location switzerlandnorth
az storage account create --name <storage-name> --resource-group rg-currency-converter --location switzerlandnorth --sku Standard_LRS
az functionapp create --name <function-app-name> --resource-group rg-currency-converter \
  --storage-account <storage-name> --consumption-plan-location switzerlandnorth \
  --runtime python --runtime-version 3.12 --functions-version 4 --os-type linux

# 3. Autoriser le frontend à appeler la Function (CORS)
az functionapp cors add --name <function-app-name> --resource-group rg-currency-converter \
  --allowed-origins "http://127.0.0.1:8000" "https://currency-converter-n35g.onrender.com"

# 4. Déploiement du code
cd azure_function
func azure functionapp publish <function-app-name> --python
```

Puis renseigner `AZURE_FUNCTION_BASE_URL=https://<function-app-name>.azurewebsites.net` dans `.env`.

---

###  Lancer les tests

```bash
# Avec Docker
docker compose exec web python manage.py test

# En local
env $(cat .env.test | xargs) python manage.py test
```

---

###  Auteur

**Franchir Madzou**
Étudiant en Web Solution Architecture — ITS ICT Piemonte

[![GitHub](https://img.shields.io/badge/GitHub-Fred0242-black?logo=github)](https://github.com/Fred0242)

---
---

## 🇮🇹 Convertitore di Valute

Applicazione web per la conversione di valute in tempo reale, sviluppata con Python/Django e distribuita in produzione su Render.

###  Avviare il progetto (Docker)

```bash
git clone git@github.com:Fred0242/currency-converter.git
cd currency-converter
cp .env.example .env
# Compila le variabili in .env
docker compose up --build
# Accedi all'app su http://127.0.0.1:8000
```

---

###  Funzionalità

-  Conversione in tempo reale tramite l'API [Frankfurter](https://www.frankfurter.app/)
-  Bandiere dei paesi per ogni valuta
-  Valute supportate : EUR, USD, GBP, JPY, CHF, CAD, AUD, XAF (Franco CFA)
-  Autenticazione (registrazione, accesso, disconnessione)
-  Storico personale delle conversioni (utenti connessi)
-  Frontend in `fetch()` (HTTP trigger): il form scrive/legge i dati tramite chiamate HTTP JSON, senza ricaricare la pagina
-  Storico delle conversioni persistito su **Azure Table Storage**, tramite una **Azure Function** (HTTP trigger)
-  Interfaccia responsive e moderna

---

###  Stack tecnologico

| Tecnologia | Ruolo |
|---|---|
| Python 3.13 | Linguaggio principale |
| Django 5.x | Framework web |
| PostgreSQL 16 | Database (account, storico locale) |
| Azure Functions (Python) | API HTTP trigger (scrittura/lettura conversioni) |
| Azure Table Storage | Persistenza dello storico lato Azure |
| Docker + Compose | Containerizzazione |
| GitHub Actions | CI/CD |
| Render | Deploy in produzione |
| Gunicorn | Server WSGI produzione |
| Whitenoise | File statici |

---

###  Architettura del progetto

```
currency_converter/
│
├── core/                   ← Configurazione Django
├── converter/              ← App principale (form + API JSON convert_api / history_api)
├── users/                  ← App autenticazione
├── azure_function/          ← Azure Function (Python, HTTP trigger + Table Storage)
├── .github/workflows/      ← CI/CD GitHub Actions
├── Dockerfile              ← Immagine Docker
├── docker-compose.yml      ← Orchestrazione locale
└── requirements.txt        ← Dipendenze Python
```

---

###  Installazione locale (via Docker)

#### Prerequisiti
- Docker Desktop
- Git

#### Passaggi

```bash
# 1. Clona il repository
git clone git@github.com:Fred0242/currency-converter.git
cd currency-converter

# 2. Crea il file .env
cp .env.example .env
# Compila le variabili in .env

# 3. Avvia l'app
docker compose up --build

# 4. Accedi all'app
# http://127.0.0.1:8000
```

---

###  API HTTP (scrittura / lettura)

Il form di conversione non invia più un POST classico con ricaricamento della pagina: il frontend usa `fetch()` in JSON verso un'API HTTP.

| Endpoint | Metodo | Ruolo |
|---|---|---|
| `/api/convert/` (Django) | POST | Calcola e scrive una conversione (storico salvato se loggato) |
| `/api/history/` (Django) | GET | Legge lo storico dell'utente connesso |
| `{AZURE_FUNCTION_BASE_URL}/api/convert` | POST | Stessa logica, eseguita da una **Azure Function** (HTTP trigger) |
| `{AZURE_FUNCTION_BASE_URL}/api/history/{username}` | GET | Legge lo storico da **Azure Table Storage** |

Il frontend passa automaticamente all'Azure Function se la variabile d'ambiente `AZURE_FUNCTION_BASE_URL` è impostata (vedi `.env.example`); altrimenti usa l'API Django locale.

---

###  Azure Function (HTTP trigger + Table Storage)

La cartella [`azure_function/`](azure_function/) contiene una Azure Function Python (modello v2) con due endpoint HTTP trigger che scrivono/leggono lo storico delle conversioni in una tabella Azure (`ConversionHistory`), indipendentemente dal database PostgreSQL. Vedi la sezione francese sopra per i comandi di deploy (`az group create`, `az functionapp create`, `func azure functionapp publish`, ecc.).

---

### Eseguire i test

```bash
# Con Docker
docker compose exec web python manage.py test

# In locale
env $(cat .env.test | xargs) python manage.py test
```

---

###  Autore

**Franchir Madzou**
Studente in Web Solution Architecture — ITS ICT Piemonte

[![GitHub](https://img.shields.io/badge/GitHub-Fred0242-black?logo=github)](https://github.com/Fred0242)