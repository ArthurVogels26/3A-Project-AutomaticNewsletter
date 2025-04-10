
import re
import requests
from bs4 import BeautifulSoup
import os
import pymupdf
from urllib.parse import urlparse
from processing.extracted_data import ExtractedData

class DataExtractor:
    def __init__(self):
        # Utiliser une session pour réutiliser les connexions HTTP
        self.session = requests.Session()

    def extract_arxiv(self, arxiv_id):
        # Récupérer les métadonnées via l'API arXiv
        url = f'https://export.arxiv.org/api/query?id_list={arxiv_id}'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'xml')
        entry = soup.find('entry')
        if not entry:
            raise ValueError("Aucune entrée trouvée pour l'ID arXiv fourni.")

        title = entry.title.text.strip()

        metadata = {
            'authors': [author.find('name').text for author in entry.find_all('author')],
            'summary': entry.summary.text.strip(),
            'publication_date': entry.published.text,
            'categories': entry.find('arxiv:primary_category')['term'],
        }

        # Télécharger le PDF et extraire le texte
        pdf_url = entry.find('link', title='pdf')['href']
        pdf_response = requests.get(pdf_url)
        pdf_path = f"{arxiv_id}.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(pdf_response.content)

        try:
            with pymupdf.open(pdf_path) as doc:
                content = ""
                for page in doc:
                    content += page.get_text()
        except Exception as e:
            content = f"Erreur lors de l'extraction du texte PDF: {e}"
        finally:
            os.remove(pdf_path)

        return {
            'title': title,
            'content': content,
            'metadata': metadata,
            'links': [f'https://arxiv.org/abs/{arxiv_id}']
        }

    def extract_github(self, repo_url):
        # Extraire le propriétaire et le nom du dépôt à partir de l'URL
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError("URL GitHub invalide. Format attendu : https://github.com/owner/repo")
        repo_owner, repo_name = path_parts[:2]

        # Récupérer les métadonnées via l'API GitHub
        api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}'
        response = requests.get(api_url)
        if response.status_code != 200:
            raise ValueError(f"Erreur lors de la récupération des données GitHub: {response.status_code}")
        repo_data = response.json()

        title = repo_data.get('name', "Nom non disponible")

        # Récupérer le README via l'API GitHub
        readme_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/readme'
        response = requests.get(readme_url, headers={'Accept': 'application/vnd.github.v3.raw'})
        content =  response.text if response.status_code == 200 else "README non disponible."

        metadata = {
            'owner': repo_data.get('owner', {}).get('login'),
            'description': repo_data.get('description'),
            'language': repo_data.get('language'),
            'created_at': repo_data.get('created_at'),
            'updated_at': repo_data.get('updated_at'),
        }

        return {
            'title': title,
            'content': content,
            'metadata': metadata
        }

    def extract_huggingface_model(self, model_id):
        # Récupérer les métadonnées via l'API HuggingFace
        api_url = f'https://huggingface.co/api/models/{model_id}'
        response = requests.get(api_url)
        if response.status_code != 200:
            raise ValueError(f"Erreur lors de la récupération des données HuggingFace: {response.status_code}")
        model_data = response.json()

        title = model_data.get('modelId', "Modèle non disponible")
        content = self._fetch_huggingface_readme(model_id)

        metadata = {
            'author': model_data.get('author'),
            'tags': model_data.get('tags'),
            'pipeline_tag': model_data.get('pipeline_tag'),
            'cardData': model_data.get('cardData')
        }

        # Extraire les papiers arXiv mentionnés dans les tags
        arxiv_papers = self._extract_arxiv_from_tags_for_hugginface(model_data.get('tags', []))
        if arxiv_papers:
            metadata['arxiv_papers'] = arxiv_papers

        return {
            'title': title,
            'content': content,
            'metadata': metadata
        }

    def extract_huggingface_dataset(self, dataset_id):
        # Récupérer les métadonnées via l'API HuggingFace
        api_url = f'https://huggingface.co/api/datasets/{dataset_id}'
        response = requests.get(api_url)
        if response.status_code != 200:
            raise ValueError(f"Erreur lors de la récupération des données HuggingFace: {response.status_code}")
        dataset_data = response.json()

        title = dataset_data.get('datasetId', "Dataset non disponible")
        content = self._fetch_huggingface_readme(f'datasets/{dataset_id}')

        metadata = {
            'author': dataset_data.get('author'),
            'tags': dataset_data.get('tags'),
            'features': dataset_data.get('features'),
            'cardData': dataset_data.get('cardData')
        }

        # Extraire les papiers arXiv mentionnés dans les tags
        arxiv_papers = self._extract_arxiv_from_tags_for_hugginface(dataset_data.get('tags', []))
        if arxiv_papers:
            metadata['arxiv_papers'] = arxiv_papers

        return {
            'title': title,
            'content': content,
            'metadata': metadata
        }
    
    def extract_huggingface_blog(self, blog_url):
        """
        Scrape un article de blog Hugging Face.
        """
        response = requests.get(blog_url)
        
        if response.status_code != 200:
            raise ValueError(f"Erreur lors de la récupération du blog: {response.status_code}")

        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "Titre non disponible"

        content_blocks = soup.find_all(['p', 'h2', 'h3', 'li'])
        content = "\n".join([block.get_text().strip() for block in content_blocks])

        metadata = {}
        author_tag = soup.find('a', {'class': 'author'})
        metadata['author'] = author_tag.text.strip() if author_tag else "Auteur inconnu"

        date_tag = soup.find('time')
        metadata['publication_date'] = date_tag.text.strip() if date_tag else "Date inconnue"

        tags_section = soup.find('div', {'class': 'tags'})
        metadata['tags'] = [tag.text.strip() for tag in tags_section.find_all('a')] if tags_section else []

        return {
            'title': title,
            'content': content,
            'metadata': metadata
        }
        
    def extract_huggingface_space(self, space_id):
        """
        Scrape un Hugging Face Space pour récupérer ses informations.
        """
        url = f'https://huggingface.co/spaces/{space_id}'
        response = requests.get(url)

        if response.status_code != 200:
            raise ValueError(f"Erreur lors de la récupération du Space: {response.status_code}")

        soup = BeautifulSoup(response.content, 'html.parser')
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "Nom non disponible"
        description_tag = soup.find('meta', {'property': 'og:description'})
        description = description_tag["content"].strip() if description_tag else "Description non disponible"
        creator_tag = soup.find('a', {'class': 'author'})
        creator = creator_tag.text.strip() if creator_tag else "Créateur inconnu"
        tags_section = soup.find_all('span', {'class': 'tag'})
        tags = [tag.text.strip() for tag in tags_section] if tags_section else []
        content_blocks = soup.find_all(['p', 'h2', 'h3', 'li'])
        content = "\n".join([block.get_text().strip() for block in content_blocks])

        metadata = {
            'creator': creator,
            'description': description,
            'tags': tags
        }

        return {
            'title': title,
            'content': content,
            'metadata': metadata
        }

    def _fetch_huggingface_readme(self, identifier):
        """
        Méthode interne pour récupérer le README d'un modèle ou d'un dataset HuggingFace.
        """
        possible_readme_filenames = ['README.md', 'README.rst', 'README.txt']
        possible_branches = ['main', 'master']
        readme_content = "README non disponible."

        for branch in possible_branches:
            for filename in possible_readme_filenames:
                readme_url = f'https://huggingface.co/{identifier}/resolve/{branch}/{filename}'
                readme_response = requests.get(readme_url)
                if readme_response.status_code == 200:
                    readme_content = readme_response.text
                    return readme_content  # Retourner dès que le README est trouvé

        return readme_content

    def _extract_arxiv_from_tags_for_hugginface(self, tags):
        """
        Méthode interne pour extraire les papiers arXiv à partir des tags présent sur une page huggingface.
        Retourne une liste de dictionnaires contenant les informations des papiers arXiv.
        """
        arxiv_papers = []
        arxiv_pattern = re.compile(r'arxiv:(\d{4}\.\d{5})')

        for tag in tags:
            match = arxiv_pattern.match(tag)
            if match:
                arxiv_id = match.group(1)
                try:
                    arxiv_data = self.extract_arxiv(arxiv_id)
                    arxiv_papers.append(arxiv_data)
                except Exception as e:
                    arxiv_papers.append({'arxiv_id': arxiv_id, 'error': str(e)})

        return arxiv_papers if arxiv_papers else None

    def extract_blog(self, blog_url):
        response = requests.get(blog_url)
        if response.status_code != 200:
            raise ValueError(f"Erreur lors de la récupération de l'article de blog: {response.status_code}")
        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else "Titre non disponible"

        # Extraction du contenu principal
        # Partie à ajuster
        paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'li'])
        content = '\n'.join([para.get_text().strip() for para in paragraphs])

        metadata = {
            'url': blog_url
        }

        return {
            'title': title,
            'content': content,
            'metadata': metadata
        }

    def get_source_type(self, url_or_id):
        parsed_url = urlparse(url_or_id)
        path_parts = parsed_url.path.strip('/').split('/')

        if 'arxiv.org' in parsed_url.netloc:
            return 'arxiv', path_parts[-1].replace('abs/', '').replace('pdf/', '').replace('.pdf', '').strip()

        elif 'github.com' in parsed_url.netloc:
            return 'github', url_or_id

        elif 'huggingface.co' in parsed_url.netloc:
            if len(path_parts) < 2:
                raise ValueError("URL Hugging Face invalide. Format attendu : https://huggingface.co/owner/model ou autres variantes.")

            first_part = path_parts[0].lower()

            if first_part == "blog":
                return 'huggingface_blog', url_or_id
            elif first_part == "spaces":
                return 'huggingface_space', '/'.join(path_parts[1:3])
            elif first_part == "datasets":
                return 'huggingface_dataset', '/'.join(path_parts[1:3])
            else:
                return 'huggingface_model', '/'.join(path_parts[:2])
        else:
            return 'blog', url_or_id 


    def convert_to_extracted_data(self, source_type, identifier, extracted_result):
        """Convertir les résultats extraits en une instance d'ExtractedData."""
        
        if source_type == 'arxiv':
            title = extracted_result.get('title', None)
            content = extracted_result.get('content', None)
            metadata = extracted_result.get('metadata', {})
        elif source_type == 'github':
            title = extracted_result.get('title', None)
            content = extracted_result.get('content', None)
            metadata = extracted_result.get('metadata', {})
        elif source_type == 'huggingface_model':
            title = extracted_result.get('title', None)
            content = extracted_result.get('content', None)
            metadata = extracted_result.get('metadata', {})
        elif source_type == 'huggingface_dataset':
            title = extracted_result.get('title', None)
            content = extracted_result.get('content', None)
            metadata = extracted_result.get('metadata', {})
        else: 
            title = extracted_result.get('title', None)
            content = extracted_result.get('content', None)
            metadata = extracted_result.get('metadata', {})

        # Créer une instance d'ExtractedData
        return ExtractedData(source_type, identifier, title, content, metadata)

    def extract(self, url_or_id):
        source_type, identifier = self.get_source_type(url_or_id)
    
        if source_type == 'arxiv':
            result = self.extract_arxiv(identifier)
        elif source_type == 'github':
            result = self.extract_github(identifier)
        elif source_type == 'huggingface_model':
            result = self.extract_huggingface_model(identifier)
        elif source_type == 'huggingface_dataset':
            result = self.extract_huggingface_dataset(identifier)
        elif source_type == 'huggingface_blog':
            result = self.extract_huggingface_blog(identifier)
        elif source_type == 'huggingface_space':
            result = self.extract_huggingface_space(identifier)
        elif source_type == 'blog':
            result = self.extract_blog(identifier)
        
        # Convertir le résultat en un format uniforme
        return self.convert_to_extracted_data(source_type, identifier, result)

