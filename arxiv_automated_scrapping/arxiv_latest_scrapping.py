import requests
from datetime import datetime, timezone, timedelta
import json
import os
from bs4 import BeautifulSoup
import time
import re

def fetch_recent_arxiv_articles(query="cat:cs.AI", max_results=100, start=0):
    """
    Récupère les articles ArXiv les plus récents dans les catégories spécifiées.
    
    Args:
        query: La requête de recherche
        max_results: Nombre maximum de résultats à retourner (max 100 selon API ArXiv)
        start: Index de départ pour la pagination
        
    Returns:
        Le contenu XML de la réponse
    """
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    # Respecter les limites de l'API ArXiv (min 3 secondes entre requêtes)
    print(f"⏳ Délai de pause pour respecter les limites de l'API ArXiv...")
    time.sleep(3)
    
    print(f"📡 Requête API ArXiv: start={start}, max_results={max_results}")
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API ArXiv: {e}")
        if hasattr(response, 'status_code'):
            print(f"Code d'erreur: {response.status_code}")
        if hasattr(response, 'text'):
            print(f"Réponse: {response.text[:500]}...")
        raise

def extract_article_id(link):
    """
    Extrait l'identifiant unique de l'article à partir de son lien.
    
    Args:
        link: URL ou identifiant d'ArXiv
        
    Returns:
        Identifiant unique de l'article
    """
    # Les ID d'ArXiv sont généralement de la forme: http://arxiv.org/abs/XXXX.XXXXX ou XXXX.XXXXX
    if not link:
        return None
    
    # Chercher l'identifiant dans l'URL
    match = re.search(r'abs/([^/]+)$', link)
    if match:
        return match.group(1)
    
    # Sinon utiliser le lien entier comme ID
    return link

def parse_arxiv_articles(xml_data, target_categories, strict_category=False):
    """
    Parse le contenu XML d'ArXiv pour extraire les informations des articles.
    
    Args:
        xml_data: Contenu XML retourné par l'API ArXiv
        target_categories: Liste des catégories à inclure
        strict_category: Si True, ne garde que les articles dont la catégorie principale correspond
                         Si False, inclut les articles qui ont une des catégories cibles parmi leurs catégories
        
    Returns:
        Une liste d'articles sous forme de dictionnaires
    """
    try:
        soup = BeautifulSoup(xml_data, features="xml")
    except:
        print("⚠️ Parser XML non disponible, utilisation du parser HTML")
        soup = BeautifulSoup(xml_data, "html.parser")
    
    entries = soup.find_all("entry")
    print(f"📄 Nombre d'entrées trouvées dans le XML: {len(entries)}")
    
    articles = []
    filtered_out_count = 0

    for entry in entries:
        try:
            # Extraire la catégorie principale
            primary_category = entry.find("arxiv:primary_category")
            if not primary_category:
                primary_category = entry.find("category")
            
            primary_cat = primary_category.get("term") if primary_category else "Unknown"
            
            # Extraire toutes les catégories (principales et secondaires)
            all_categories = []
            if primary_cat != "Unknown":
                all_categories.append(primary_cat)
                
            # Ajouter les catégories secondaires
            category_tags = entry.find_all("category")
            for cat_tag in category_tags:
                cat_term = cat_tag.get("term")
                if cat_term and cat_term not in all_categories:
                    all_categories.append(cat_term)
            
            # Vérifier si l'article correspond aux critères de catégorie
            category_match = False
            
            if not target_categories:  # Si aucune catégorie n'est spécifiée, on accepte tout
                category_match = True
            elif strict_category:
                # Mode strict: la catégorie principale doit correspondre exactement
                category_match = primary_cat in target_categories
            else:
                # Mode inclusif: n'importe quelle catégorie de l'article peut correspondre
                category_match = any(cat in target_categories for cat in all_categories)
            
            # Passer à l'entrée suivante si la catégorie ne correspond pas
            if not category_match:
                filtered_out_count += 1
                continue
            
            # Extraire les informations de l'article
            title = ""
            if entry.title:
                title = entry.title.string.strip() if hasattr(entry.title, 'string') else str(entry.title).strip()
            
            summary = "Résumé non disponible."
            if entry.summary:
                summary = entry.summary.string.strip() if hasattr(entry.summary, 'string') else str(entry.summary).strip()
            
            link = ""
            if entry.id:
                link = entry.id.string.strip() if hasattr(entry.id, 'string') else str(entry.id).strip()
            
            # Extraire l'identifiant unique
            article_id = extract_article_id(link)
            
            published_date_str = ""
            if entry.published:
                published_date_str = entry.published.string.strip() if hasattr(entry.published, 'string') else str(entry.published).strip()
            
            # Extraire les auteurs
            authors = []
            author_tags = entry.find_all("author")
            for author in author_tags:
                name_elem = author.find('name')
                if name_elem:
                    author_name = name_elem.string.strip() if hasattr(name_elem, 'string') else str(name_elem).strip()
                    authors.append(author_name)
            
            # Ajouter l'article avec toutes ses catégories
            articles.append({
                "id": article_id,
                "title": title,
                "authors": authors,
                "published_date": published_date_str,
                "category": primary_cat,   # Catégorie principale
                "all_categories": all_categories,  # Toutes les catégories
                "summary": summary,
                "link": link
            })
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse d'un article: {e}")
            filtered_out_count += 1
            continue

    # Ajouter des statistiques supplémentaires
    categories_count = {}
    for article in articles:
        cat = article["category"]
        if cat in categories_count:
            categories_count[cat] += 1
        else:
            categories_count[cat] = 1
    
    # Afficher les statistiques par catégorie
    for cat, count in categories_count.items():
        print(f"   - {cat}: {count} articles")
    
    print(f"✅ Articles inclus: {len(articles)}, articles filtrés: {filtered_out_count}")
    return articles

def get_latest_arxiv_articles(categories=None, max_articles=500, strict_category=False, callback=None):
    """
    Récupère les articles les plus récents d'ArXiv sans duplication.
    
    Args:
        categories: Liste des catégories ArXiv à inclure ou None pour toutes
        max_articles: Nombre maximum d'articles à récupérer
        strict_category: Si True, ne considère que la catégorie principale
                         Si False, considère toutes les catégories de l'article
        callback: Fonction appelée pour informer de la progression (pour l'interface utilisateur)
        
    Returns:
        Liste d'articles uniques sous forme de dictionnaires
    """
    # Construire la requête
    if categories and len(categories) > 0:
        query = " OR ".join([f"cat:{category}" for category in categories])
        print(f"🔍 Recherche d'articles pour les catégories: {categories}")
        print(f"🔍 Mode de filtrage: {'Strict (catégorie principale uniquement)' if strict_category else 'Inclusif (toutes catégories)'}")
        
        # Informer l'UI si le callback existe
        if callback:
            callback(f"Recherche dans {len(categories)} catégories: {', '.join(categories)}")
    else:
        query = "all"  # Tous les articles
        print("🔍 Recherche sur toutes les catégories ArXiv")
        if callback:
            callback("Recherche sur toutes les catégories")
    
    print(f"🎯 Récupération des {max_articles} articles les plus récents...")
    
    all_articles = []
    seen_ids = set()  # Pour suivre les articles déjà vus
    start = 0
    batch_size = 100  # Taille maximale par requête selon l'API ArXiv
    empty_response_count = 0
    max_empty_responses = 5  # Arrêt après 5 réponses vides consécutives
    duplicates_count = 0
    
    while len(all_articles) < max_articles and empty_response_count < max_empty_responses:
        try:
            batch_num = len(all_articles) // batch_size + 1
            print(f"🔄 Récupération du lot {batch_num}: articles {start+1} à {start+batch_size}")
            if callback:
                callback(f"Récupération du lot {batch_num}: articles {start+1} à {start+batch_size}")
            
            # Récupérer un lot d'articles
            xml_data = fetch_recent_arxiv_articles(query=query, max_results=batch_size, start=start)
            articles_batch = parse_arxiv_articles(
                xml_data, 
                target_categories=categories, 
                strict_category=strict_category
            )
            
            if not articles_batch:
                empty_response_count += 1
                print(f"⚠️ Lot vide ({empty_response_count}/{max_empty_responses})")
                if callback:
                    callback(f"Lot {batch_num} vide ({empty_response_count}/{max_empty_responses})", level="warning")
                
                if empty_response_count >= max_empty_responses:
                    print("🛑 Trop de lots vides consécutifs, arrêt de la récupération")
                    if callback:
                        callback("Trop de lots vides consécutifs, arrêt de la récupération", level="warning")
                    break
                start += batch_size
                continue
            
            # Réinitialiser le compteur si on a des résultats
            empty_response_count = 0
            
            # Ajouter uniquement les articles non vus
            added_count = 0
            new_duplicates = 0
            for article in articles_batch:
                article_id = article.get("id")
                if article_id and article_id not in seen_ids:
                    all_articles.append(article)
                    seen_ids.add(article_id)
                    added_count += 1
                else:
                    new_duplicates += 1
                    duplicates_count += 1
            
            print(f"📊 Articles uniques ajoutés dans ce lot: {added_count}")
            print(f"📊 Total d'articles uniques: {len(all_articles)}/{max_articles}")
            
            if callback:
                # Envoyer des informations détaillées sur ce lot
                categories_in_batch = {}
                for article in articles_batch:
                    cat = article["category"]
                    if cat in categories_in_batch:
                        categories_in_batch[cat] += 1
                    else:
                        categories_in_batch[cat] = 1
                
                cat_details = ", ".join([f"{cat}: {count}" for cat, count in categories_in_batch.items()])
                callback(f"Lot {batch_num}: {added_count} nouveaux articles, {new_duplicates} doublons ({cat_details})", 
                        batch_info={"total": len(all_articles), "duplicates": duplicates_count})
            
            # Si on n'a pas ajouté de nouveaux articles, possible que nous ayons atteint la fin
            if added_count == 0:
                print("⚠️ Aucun nouvel article unique dans ce lot, passage au suivant...")
                if callback:
                    callback("Aucun nouvel article unique dans ce lot", level="warning")
                    
                if len(articles_batch) < batch_size:
                    print("🛑 Moins d'articles que demandé et pas de nouveaux articles, arrêt de la récupération")
                    if callback:
                        callback("Fin des résultats atteinte", level="warning")
                    break
            
            # Passer au lot suivant
            start += batch_size
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du lot: {e}")
            if callback:
                callback(f"Erreur: {str(e)}", level="error")
            time.sleep(5)  # Attendre plus longtemps en cas d'erreur
    
    print(f"✅ Récupération terminée. {len(all_articles)} articles uniques récupérés.")
    if callback:
        callback(f"Récupération terminée avec {len(all_articles)} articles uniques", level="success")
    
    # Retourner uniquement le nombre demandé d'articles (triés par date)
    sorted_articles = sorted(
        all_articles,
        key=lambda x: x.get('published_date', ''), 
        reverse=True
    )
    return sorted_articles[:max_articles]

def filter_articles_by_keywords(articles, keywords, field="title"):
    """
    Filtre les articles par mots-clés dans un champ spécifié.
    """
    if not keywords:
        return articles
        
    filtered_articles = []
    for article in articles:
        text = article.get(field, "").lower()
        if any(keyword.lower() in text for keyword in keywords):
            filtered_articles.append(article)
            
    return filtered_articles

def filter_articles_by_keywords_multi(articles, keywords):
    """
    Filtre les articles par mots-clés sur plusieurs champs simultanément:
    titre, résumé et catégories.
    
    Args:
        articles: Liste des articles à filtrer
        keywords: Liste des mots-clés recherchés
        
    Returns:
        Liste des articles correspondant à au moins un mot-clé
    """
    if not keywords:
        return articles
    
    filtered_articles = []
    for article in articles:
        # Créer un texte combiné pour la recherche
        title = article.get("title", "").lower()
        summary = article.get("summary", "").lower()
        
        # Inclure toutes les catégories pour la recherche
        all_categories = article.get("all_categories", [])
        categories_text = " ".join(all_categories).lower()
        
        # Rechercher dans tous les champs
        combined_text = f"{title} {summary} {categories_text}"
        
        # Vérifier si au moins un mot-clé correspond
        if any(keyword.lower() in combined_text for keyword in keywords):
            filtered_articles.append(article)
    
    return filtered_articles

def export_to_json(articles, filename="arxiv_articles.json"):
    """
    Exporte les articles au format JSON.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"📁 Articles exportés vers {filename}")

if __name__ == "__main__":
    # Liste des catégories principales liées à l'IA
    target_categories = ["cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.NE", "cs.RO", "stat.ML"]

    try:
        # Récupérer les articles les plus récents sans duplication
        articles = get_latest_arxiv_articles(
            categories=target_categories,
            max_articles=200,  # Par défaut, récupérer les 200 articles les plus récents
            strict_category=False  # Mode de filtrage par défaut
        )
        
        # Filtrer optionnellement par mots-clés
        keywords = ["transformer", "llm", "large language model", "gpt", "attention"]
        filtered_articles = filter_articles_by_keywords_multi(articles, keywords)
        
        # Afficher un résumé
        print(f"\n📊 Récapitulatif:")
        print(f"   - Articles récupérés: {len(articles)}")
        print(f"   - Articles filtrés par mots-clés: {len(filtered_articles)}")
        
        # Afficher les 10 premiers articles
        print("\n📑 Aperçu des articles récents:")
        for i, article in enumerate(articles[:10]):
            print(f"  {i+1}. {article['title']} ({article['category']})")
            print(f"     Date: {article['published_date']}")
            print(f"     Auteurs: {', '.join(article['authors'])}")
            print(f"     Lien: {article['link']}")
            print()
            
    except Exception as e:
        print(f"❌ Erreur globale: {e}")
