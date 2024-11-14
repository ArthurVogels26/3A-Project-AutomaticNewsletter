# 3A-Project-AutomaticNewsletter

    data_extractor.py sert à extraire et centraliser des métadonnées et du contenu de plusieurs plateformes de partage de connaissances et de développement, telles que Arxiv, GitHub, Hugging Face et des blogs. Ce script permet d’obtenir des informations de base et du contenu détaillé pour un accès simplifié aux ressources d'apprentissage et de recherche.

## Fonctionnalités

    Arxiv : Extraction des métadonnées d'articles scientifiques via leur identifiant Arxiv et téléchargement du contenu en PDF.
    GitHub : Récupération des informations d'un dépôt (nom, propriétaire, étoiles, forks, etc.) et du contenu du README.
    Hugging Face : Extraction des métadonnées des modèles et datasets, avec tentative de récupération du README et des articles Arxiv associés.
    Blogs : Extraction du titre et du contenu principal d'un article de blog.