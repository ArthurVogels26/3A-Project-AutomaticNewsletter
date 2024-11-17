# 3A-Project-AutomaticNewsletter

`data_extractor.py` est un outil Python conçu pour automatiser l'extraction et la centralisation de métadonnées et de contenu provenant de diverses plateformes de partage de connaissances et de développement, notamment **Arxiv**, **GitHub**, **Hugging Face**, ainsi que des **blogs**. Ce script facilite l’accès aux informations essentielles des ressources d'apprentissage et de recherche en rendant disponibles les métadonnées et le contenu détaillé de chaque source.

## Fonctionnalités

- **Arxiv** : Récupère les métadonnées d'articles scientifiques grâce à leur identifiant Arxiv, incluant le titre, les auteurs, le résumé, et les catégories. Télécharge également le PDF et en extrait le texte.
- **GitHub** : Récupère des informations clés d'un dépôt GitHub, telles que le nom, le propriétaire, le nombre d'étoiles, le nombre de forks, la langue principale, et le contenu du fichier README.
- **Hugging Face** : Extrait les métadonnées des modèles et datasets disponibles sur Hugging Face, comme le nombre de téléchargements, les tags, et les informations de l’auteur. Tente également de récupérer le README et les articles Arxiv associés aux modèles et datasets.
- **Blogs** : Récupère le titre et le contenu principal d'articles de blog pour une lecture simplifiée et centralisée.

## Installation

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/votre-utilisateur/3A-Project-AutomaticNewsletter.git

2. Installer les dépendences (voir requirement.txt)