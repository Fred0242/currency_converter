#  Currency Converter

![CI](https://github.com/Fred0242/currency-converter/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.x-green?logo=django)
![Docker](https://img.shields.io/badge/Docker-✓-blue?logo=docker)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)
![Render](https://img.shields.io/badge/Deployed%20on-Render-purple?logo=render)

> 🇫🇷 Français | 🇮🇹 [Italiano](#-convertitore-di-valute)

---

## 🇫🇷 Convertisseur de Devises

Application web de conversion de devises en temps réel, développée avec Python/Django et déployée en production sur Render.

###  Démo en ligne

 **[https://currency-converter-n35g.onrender.com](https://currency-converter-n35g.onrender.com)**

---

###  Fonctionnalités

-  Conversion en temps réel via l'API [Frankfurter](https://www.frankfurter.app/)
-  Drapeaux des pays pour chaque devise
-  Devises supportées : EUR, USD, GBP, JPY, CHF, CAD, AUD, XAF (Franc CFA)
-  Authentification (inscription, connexion, déconnexion)
-  Historique personnel des conversions (utilisateurs connectés)
-  Interface responsive et moderne

---

###  Stack technique

| Technologie | Rôle |
|---|---|
| Python 3.13 | Langage principal |
| Django 5.x | Framework web |
| PostgreSQL 16 | Base de données |
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
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── converter/              ← App principale
│   ├── models.py           ← Modèle ConversionHistory
│   ├── views.py            ← Logique de conversion
│   ├── services.py         ← Appel API Frankfurter
│   ├── urls.py
│   ├── templates/
│   └── tests.py
│
├── users/                  ← App authentification
│   ├── views.py
│   ├── urls.py
│   └── templates/
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

###  Demo online

 **[https://currency-converter-n35g.onrender.com](https://currency-converter-n35g.onrender.com)**

---

###  Funzionalità

-  Conversione in tempo reale tramite l'API [Frankfurter](https://www.frankfurter.app/)
-  Bandiere dei paesi per ogni valuta
-  Valute supportate : EUR, USD, GBP, JPY, CHF, CAD, AUD, XAF (Franco CFA)
-  Autenticazione (registrazione, accesso, disconnessione)
-  Storico personale delle conversioni (utenti connessi)
-  Interfaccia responsive e moderna

---

###  Stack tecnologico

| Tecnologia | Ruolo |
|---|---|
| Python 3.13 | Linguaggio principale |
| Django 5.x | Framework web |
| PostgreSQL 16 | Database |
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
├── converter/              ← App principale
├── users/                  ← App autenticazione
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