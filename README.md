# 3A-Project-AutomaticNewsletter

Cet outil Python est conçu pour automatiser l'extraction et la centralisation de métadonnées de contenu provenant de diverses plateformes de partage de connaissances et de développement, notamment **Arxiv**, **GitHub**, **Hugging Face**, **Reddit** ainsi que des **blogs** pour ensuite en faire des résumés. Ce script facilite l’accès aux informations essentielles des documents étudié.

## Fonctionnalités

- **Arxiv** : Récupère les métadonnées d'articles scientifiques grâce à leur identifiant Arxiv, incluant le titre, les auteurs, le résumé, et les catégories. Télécharge également le PDF et en extrait le texte.
- **GitHub** : Récupère des informations clés d'un dépôt GitHub, telles que le nom, le propriétaire, le nombre d'étoiles, le nombre de forks, la langue principale, et le contenu du fichier README.
- **Hugging Face** : Extrait les métadonnées des modèles et datasets disponibles sur Hugging Face, comme le nombre de téléchargements, les tags, et les informations de l’auteur. Tente également de récupérer le README et les articles Arxiv associés aux modèles et datasets.
- **Blogs** : Récupère le titre et le contenu principal d'articles de blog pour une lecture simplifiée et centralisée.



2. Installer les dépendences (voir requirement.txt)
3. Run le frontend :
   ```bash
   python -m streamlit run .\Streamlit_front.py 