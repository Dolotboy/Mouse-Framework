# Utiliser l'image python:3.12-slim-bullseye avec GLIBC 2.31 par défaut
FROM python:3.12-slim

# Installer binutils (qui inclut objdump) et autres dépendances
RUN apt-get update && apt-get install -y sudo binutils

# Copier les dépendances Python du projet
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copier le contenu du projet dans le conteneur
COPY . /usr/src/app

# Définir le répertoire de travail
WORKDIR /usr/src/app
