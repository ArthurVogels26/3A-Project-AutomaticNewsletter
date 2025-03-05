import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

def fetch_recent_arxiv_articles(query="cat:cs.AI", max_results=200, start=0):
    """
    Récupère les articles ArXiv les plus récents dans les catégories spécifiées.
    """
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Erreur : {response.status_code}")

def parse_arxiv_articles(xml_data, target_categories):
    """
    Parse le contenu XML d'ArXiv pour extraire les informations des articles,
    y compris le résumé (summary), en filtrant par une liste de catégories principales.
    """
    soup = BeautifulSoup(xml_data, "xml")
    entries = soup.find_all("entry")
    articles = []

    for entry in entries:
        # Extraire la catégorie principale
        primary_category = entry.find("arxiv:primary_category", {"xmlns:arxiv": "http://arxiv.org/schemas/atom"})
        category = primary_category.get("term") if primary_category else "Unknown"

        # Ajouter uniquement les articles avec des catégories principales correspondantes
        if category in target_categories:
            summary = entry.summary.text.strip() if entry.summary else "Résumé non disponible."
            articles.append({
                "title": entry.title.text.strip(),
                "published_date": entry.published.text.strip(),
                "category": category,
                "summary": summary,
                "link": entry.id.text.strip()
            })

    return articles

if __name__ == "__main__":
    # Liste des catégories principales liées à l'IA
    target_categories = ["cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.NE", "cs.RO"]

    # Construire la requête ArXiv pour toutes les catégories IA
    query = " OR ".join([f"cat:{category}" for category in target_categories])

    try:
        # Récupérer les articles
        xml_data = fetch_recent_arxiv_articles(query=query, max_results=200)
        articles = parse_arxiv_articles(xml_data, target_categories=target_categories)

        # Affichage des résultats
        print("Derniers articles publiés dans les catégories principales IA sur ArXiv :\n")
        if articles:
            for i, article in enumerate(articles):
                print(f"{i+1}. Title: {article['title']}")
                print(f"   Published Date: {article['published_date']}")
                print(f"   Category: {article['category']}")
                print(f"   Summary: {article['summary']}")
                print(f"   Link: {article['link']}\n")
        else:
            print("Aucun article trouvé dans les catégories principales IA.")
    except Exception as e:
        print(f"Erreur : {e}")
