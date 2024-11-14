import requests
from bs4 import BeautifulSoup
import json
import os
import pymupdf
from urllib.parse import urlparse


class DataExtractor:
    def extract_arxiv(self, arxiv_id):
        # Récupérer les métadonnées via l'API arXiv
        url = f'https://export.arxiv.org/api/query?id_list={arxiv_id}'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'xml')
        entry = soup.find('entry')
        if not entry:
            raise ValueError("Aucune entrée trouvée pour l'ID arXiv fourni.")

        data = {
            'title': entry.title.text.strip(),
            'authors': [author.find('name').text for author in entry.find_all('author')],
            'summary': entry.summary.text.strip(),
            'published': entry.published.text,
            'categories': entry.find('arxiv:primary_category')['term'],
            'link': entry.id.text
        }

        # Télécharger le PDF et extraire le texte
        pdf_url = entry.find('link', title='pdf')['href']
        pdf_response = requests.get(pdf_url)
        pdf_path = f"{arxiv_id}.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(pdf_response.content)

        try:
            with pymupdf.open(pdf_path) as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
            data['content'] = text
        except Exception as e:
            data['content'] = f"Erreur lors de l'extraction du texte PDF: {e}"
        finally:
            os.remove(pdf_path)

        return data

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

        data = {
            'name': repo_data.get('name'),
            'owner': repo_data.get('owner', {}).get('login'),
            'description': repo_data.get('description'),
            'stars': repo_data.get('stargazers_count'),
            'forks': repo_data.get('forks_count'),
            'language': repo_data.get('language'),
            'created_at': repo_data.get('created_at'),
            'updated_at': repo_data.get('updated_at'),
            'clone_url': repo_data.get('clone_url')
        }

        # Récupérer le README via l'API GitHub
        readme_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/readme'
        readme_response = requests.get(readme_url, headers={'Accept': 'application/vnd.github.v3.raw'})
        if readme_response.status_code == 200:
            data['readme'] = readme_response.text
        else:
            data['readme'] = "README non disponible."

        return data

    def extract_huggingface(self, model_url):
        # Extraire l'ID du modèle à partir de l'URL
        parsed_url = urlparse(model_url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError("URL HuggingFace invalide. Format attendu : https://huggingface.co/owner/model")
        model_id = '/'.join(path_parts[:2])

        # Récupérer les métadonnées via l'endpoint HuggingFace
        api_url = f'https://huggingface.co/api/models/{model_id}'
        response = requests.get(api_url)
        if response.status_code != 200:
            raise ValueError(f"Erreur lors de la récupération des données HuggingFace: {response.status_code}")
        model_data = response.json()

        data = {
            'modelId': model_data.get('modelId'),
            'author': model_data.get('author'),
            'downloads': model_data.get('downloads'),
            'tags': model_data.get('tags'),
            'pipeline_tag': model_data.get('pipeline_tag'),
            'likes': model_data.get('likes'),
            'cardData': model_data.get('cardData')
        }

        # Tenter de récupérer le README via les URLs bruts
        possible_readme_filenames = ['README.md', 'README.rst', 'README.txt']
        possible_branches = ['main', 'master']
        readme_content = "README non disponible."

        for branch in possible_branches:
            for filename in possible_readme_filenames:
                readme_url = f'https://huggingface.co/{model_id}/raw/{branch}/{filename}'
                readme_response = requests.get(readme_url)
                if readme_response.status_code == 200:
                    readme_content = readme_response.text
                    break
            if readme_content != "README non disponible.":
                break

        data['readme'] = readme_content

        return data

    def extract_blog(self, blog_url):
        response = requests.get(blog_url)
        if response.status_code != 200:
            raise ValueError(f"Erreur lors de la récupération de l'article de blog: {response.status_code}")
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraction du titre
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else "Titre non disponible"

        # Extraction du contenu principal
        # Partie à ajuster
        article = soup.find('article')
        if article:
            paragraphs = article.find_all(['p', 'h1', 'h2', 'h3', 'li'])
        else:
            paragraphs = soup.find_all('p')

        content = '\n'.join([para.get_text().strip() for para in paragraphs])

        data = {
            'title': title,
            'content': content,
            'url': blog_url
        }
        return data

    def extract(self, url_or_id):
        if 'arxiv.org' in url_or_id:
            # Extraire l'ID arXiv
            arxiv_id = url_or_id.split('/')[-1].replace('abs/', '').strip()
            return self.extract_arxiv(arxiv_id)
        elif 'github.com' in url_or_id:
            return self.extract_github(url_or_id)
        elif 'huggingface.co' in url_or_id:
            return self.extract_huggingface(url_or_id)
        else:
            return self.extract_blog(url_or_id)

if __name__ == "__main__":
    extractor = DataExtractor()
    url_or_id = input("Veuillez entrer l'URL ou l'identifiant de la ressource : ")
    try:
        data = extractor.extract(url_or_id)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
