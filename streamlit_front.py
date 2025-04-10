import streamlit as st
import pandas as pd
import processing.data_extractor as d_ex
import processing.data_classifier as d_c
from summarization.summarizerAgent import generate_summary, criticize_summary, classify_document
from summarization.evaluate_rouge import evaluate_summary_with_original
from datetime import datetime, date,timedelta
import time
import requests
from bs4 import BeautifulSoup
import re
from scraping.arxiv_automated_scrapping.arxiv_latest_scrapping import (
    get_latest_arxiv_articles,
    filter_articles_by_keywords_multi
)
from scraping.reddit_scraping import get_entries_from_reddit
from scraping.huggingface_automatic_scraping import get_entries_from_huggingface

# Configuration de la page
st.set_page_config(
    page_title="Newsletter Generator",
    page_icon="todo",
    layout="wide"
)

# Initialiser les variables de session si elles n'existent pas
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'arxiv_articles' not in st.session_state:
    st.session_state.arxiv_articles = None
if 'selected_article' not in st.session_state:
    st.session_state.selected_article = None
if 'selected_url' not in st.session_state:
    st.session_state.selected_url = None

#-------------------- FONCTIONS UTILITAIRES --------------------#

def format_date(date_str):
    """Formate la date en format lisible"""
    if not date_str:
        return "Date inconnue"
    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date.strftime("%d/%m/%Y")
    except:
        return date_str

#-------------------- NAVIGATION --------------------#

def navigate_to(page_name):
    """Fonction centralisée de navigation"""
    st.session_state.page = page_name
    st.rerun()

def reset_and_go_home():
    """Réinitialise toutes les données en mémoire et retourne à l'accueil"""
    # Variables à conserver (aucune dans ce cas)
    page_only = {'page': 'home'}
    
    # Réinitialiser toute la session
    for key in list(st.session_state.keys()):
        if key not in page_only:
            del st.session_state[key]
    
    # Aller à l'accueil
    st.session_state.page = 'home'
    st.rerun()

#-------------------- EXTRACTION DE DONNÉES --------------------#

def extract_data_from_url(url_or_id):
    """
    Extrait les données d'une URL ou d'un identifiant
    
    Args:
        url_or_id: URL ou identifiant à traiter
        
    Returns:
        tuple: (données extraites, catégorie détectée, succès de l'extraction)
    """
    try:
        with st.spinner("Extraction en cours..."):
            extractor = d_ex.DataExtractor()
            data = extractor.extract(url_or_id).to_dict()
            
            # Classifier le contenu
            category, (input_tok, output_tok) = classify_document(data)
            
            # Marquer la source et harmoniser la structure de données
            data["source"] = "url"
            
            return data, category, True
    except Exception as e:
        return None, None, f"Erreur d'extraction : {e}"

def extract_arxiv_paper_content(arxiv_id):
    """
    Extrait le contenu complet d'un article ArXiv par son identifiant
    
    Args:
        arxiv_id: ID ou URL de l'article ArXiv
        
    Returns:
        dict: Les données extraites de l'article ou None en cas d'erreur
    """
    try:
        # Extraire l'ID ArXiv de l'URL si nécessaire
        match = re.search(r'abs/([^/]+)$', arxiv_id)
        if match:
            arxiv_id = match.group(1)
        
        # Utiliser l'extracteur de données existant
        url = f"https://arxiv.org/abs/{arxiv_id}"
        return extract_data_from_url(url)[0]
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du contenu ArXiv: {e}")
        return None

def prepare_arxiv_article_data(article, full_extraction=True):
    """
    Prépare les données d'un article ArXiv pour le traitement
    
    Args:
        article: Dictionnaire des métadonnées d'un article ArXiv
        full_extraction: Si True, tente d'extraire le contenu complet
        
    Returns:
        tuple: (données préparées, catégorie, succès de l'opération)
    """
    with st.spinner("Préparation des données de l'article..."):
        try:
            data = None
            
            # Tenter l'extraction complète si demandée
            if full_extraction:
                try:
                    st.info("Extraction du contenu complet de l'article...")
                    data = extract_arxiv_paper_content(article["link"])
                    
                    # Ajouter les métadonnées manquantes à partir des métadonnées ArXiv
                    if data:
                        if "title" not in data or not data["title"]:
                            data["title"] = article["title"]
                        
                        if "authors" not in data or not data["authors"]:
                            data["authors"] = article["authors"]
                except Exception as e:
                    st.warning(f"Erreur lors de l'extraction complète: {e}")
                    data = None
            
            # Si l'extraction complète a échoué ou n'a pas été demandée, utiliser les métadonnées de base
            if not data:
                if full_extraction:
                    st.warning("Utilisation des métadonnées de base car l'extraction complète a échoué.")
                
                data = {
                    "title": article["title"],
                    "authors": article["authors"],
                    "date": article["published_date"],
                    "url": article["link"],
                    "content": article["summary"],
                    "category": article["category"]
                }
            
            # Marquer la source et standardiser le format
            data["source"] = "arxiv"
            
            # Pour les articles ArXiv, la catégorie est toujours "research paper"
            category = "research paper"
            
            return data, category, True
            
        except Exception as e:
            st.error(f"Erreur lors de la préparation des données: {e}")
            return None, None, f"Erreur: {str(e)}"

#-------------------- AFFICHAGE DES ARTICLES --------------------#

def display_arxiv_articles(articles, title="Articles"):
    """
    Affiche les articles ArXiv sous forme de tableau interactif
    """
    if not articles:
        st.warning("Aucun article trouvé.")
        return
    
    st.subheader(title)
    
    # Créer un DataFrame pour l'affichage
    df = pd.DataFrame([{
        "Index": idx,
        "Titre": article["title"],
        "Auteurs": ", ".join(article["authors"]),
        "Date": format_date(article["published_date"]),
        "Catégorie": article["category"],
        "Toutes catégories": ", ".join(article.get("all_categories", [article["category"]])),
        "Résumé": article["summary"][:150] + "..." if len(article["summary"]) > 150 else article["summary"],
        "Lien": article["link"]
    } for idx, article in enumerate(articles)])
    
    # Afficher le tableau
    st.dataframe(df, use_container_width=True)

def display_article_details(article):
    """
    Affiche les détails d'un article spécifique dans un expander
    """
    with st.expander(f"{article['title']}", expanded=True):
        st.markdown(f"**Auteurs:** {', '.join(article['authors'])}")
        st.markdown(f"**Date:** {format_date(article['published_date'])}")
        st.markdown(f"**Catégorie principale:** {article['category']}")
        if "all_categories" in article:
            st.markdown(f"**Toutes les catégories:** {', '.join(article['all_categories'])}")
        st.markdown(f"**Lien:** [{article['link']}]({article['link']})")
        st.markdown("**Résumé:**")
        st.markdown(article['summary'])

#-------------------- TRAITEMENT DES DONNÉES --------------------#

def save_extracted_data(data, category):
    """
    Enregistre les données extraites dans la session
    et redirige vers la page de traitement
    """
    st.session_state.extracted_data = data
    st.session_state.extracted_category = category
    navigate_to('process_data')

def process_extraction(data, category, success, source_page="home"):
    """
    Traite le résultat d'une extraction et décide de la suite
    
    Args:
        data: Données extraites
        category: Catégorie détectée
        success: Résultat de l'extraction (True/False ou message d'erreur)
        source_page: Page d'origine pour retour en arrière
    """
    if success is True:
        # Extraction réussie
        save_extracted_data(data, category)
    else:
        # Échec de l'extraction
        st.error(f"Erreur lors de l'extraction: {success}")

def generate_content_summary():
    """
    Génère un résumé du contenu extrait
    """
    try:
        with st.spinner("Résumé en cours..."):
            summary, (input_tok, output_tok) = generate_summary(st.session_state.extracted_data)
            st.session_state.summary = summary
            st.session_state.summary_price = float(input_tok)*0.150/1e6 + float(output_tok)*0.6/1e6
            return True
    except Exception as e:
        st.warning(f"Erreur lors du résumé : {e}")
        return False

def evaluate_summary_with_critique():
    """
    Génère une critique du résumé
    """
    try:
        with st.spinner("Critique en cours..."):
            review = criticize_summary(st.session_state.extracted_data, st.session_state.summary)
            st.session_state.review = review
            return True
    except Exception as e:
        st.error(f"Erreur lors de la critique: {e}")
        return False

def calculate_rouge_metrics():
    """
    Calcule les métriques ROUGE pour le résumé
    """
    try:
        with st.spinner("Calcul des métriques Rouge..."):
            original_content = st.session_state.extracted_data.get("content", "")
            rouge_scores = evaluate_summary_with_original(st.session_state.summary, original_content)
            st.session_state.rouge_scores = rouge_scores
            return True
    except Exception as e:
        st.error(f"Erreur lors de l'évaluation Rouge : {e}")
        return False

#-------------------- PAGES DE L'INTERFACE --------------------#

def show_home_page():
    """Page d'accueil avec options de navigation"""
    st.title("Générateur de Newsletter Automatique :wave:")
    st.write("""
    Bienvenue sur cette application de démonstration. Veuillez choisir une option:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Extraction par URL")
        st.write("Entrez l'URL ou l'identifiant d'une ressource pour l'extraire et la résumer.")
        if st.button("Extraction par URL 🔍", key="btn_url", use_container_width=True):
            navigate_to('regular_extraction')
            
    with col2:
        st.markdown("### Recherche sur ArXiv")
        st.write("Recherchez et filtrez des articles récents sur ArXiv pour les résumer.")
        if st.button("Recherche ArXiv 📚", key="btn_arxiv", use_container_width=True):
            navigate_to('arxiv_scraper')

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### Recherche Automatique sur HuggingFace")
        st.write("Extrait les derniers articles en vogue de HuggingFace pour les résumer.")
        if st.button("Auto-Extraction HuggingFace 🤖", key="btn_huggingface", use_container_width=True):
            navigate_to('huggingface_scraper')

    with col4:
        st.markdown("### Recherche Automatique sur Reddit")
        st.write("Extrait les derniers articles en vogue de Reddit pour les résumer.")
        if st.button("Auto-Extraction Reddit 🤖", key="btn_reddit", use_container_width=True):
            navigate_to('reddit_scraper')

def show_regular_extraction_page():
    """Page d'extraction par URL"""
    st.title("Extraction par URL :mag:")
    
    # Bouton de retour
    if st.button("← Retour à l'accueil", key="home_from_regular"):
        navigate_to('home')

    # Entrée utilisateur
    if not st.session_state.selected_url:
        url_or_id = st.text_input("Entrez l'URL ou l'identifiant de la ressource :", placeholder="Exemple : https://arxiv.org/abs/1234.56789")

        # Bouton pour lancer l'extraction
        if st.button("Extraire les données 🚀", key='extract_button'):
            if url_or_id.strip() == "":
                st.warning("Veuillez entrer un lien ou un identifiant valide.")
            else:
                data, category, success = extract_data_from_url(url_or_id)
                process_extraction(data, category, success, 'regular_extraction')
    
    else:
        data, category, success = extract_data_from_url(st.session_state.selected_url)
        st.session_state.selected_url = None
        process_extraction(data, category, success, 'regular_extraction')

def show_arxiv_scraper_page():
    """Page du scrapper ArXiv"""
    st.title("Recherche sur ArXiv 📚")
    
    # Bouton de retour
    if st.button("← Retour à l'accueil", key="home_from_arxiv"):
        navigate_to('home')

    st.markdown("""
    Recherchez et filtrez les articles récents d'ArXiv.
    """)
    
    # Sidebar pour les paramètres
    with st.sidebar:
        st.header("Paramètres de recherche")
        
        # Mode de filtrage par catégorie 
        st.subheader("Mode de filtrage")
        strict_category = st.checkbox(
            "Mode strict (catégorie principale uniquement)", 
            value=False,
            help="Si activé, ne récupère que les articles dont la catégorie principale correspond exactement. "
                 "Si désactivé, inclut les articles qui ont une des catégories cibles parmi leurs catégories secondaires."
        )
        
        # Sélection des catégories
        st.subheader("Catégorie" if strict_category else "Catégories")
        categories = {
            "Intelligence Artificielle": "cs.AI",
            "Apprentissage Automatique": "cs.LG",
            "Vision par Ordinateur": "cs.CV",
            "Traitement du Langage Naturel": "cs.CL",
            "Réseaux de Neurones": "cs.NE",
            "Robotique": "cs.RO",
            "Machine Learning (Statistique)": "stat.ML"
        }
        
        # Mode de sélection de catégorie(s) selon le mode strict ou non
        if strict_category:
            category_options = list(categories.keys())
            selected_category = st.radio(
                "Sélectionnez une catégorie principale:", 
                category_options,
                index=0,
                key="primary_category"
            )
            selected_categories = [categories[selected_category]]
        else:
            selected_categories = []
            for name, cat_id in categories.items():
                if st.checkbox(name, value=False, key=f"cat_{cat_id}"):
                    selected_categories.append(cat_id)
               
        # Mots-clés pour filtrer
        st.subheader("Filtrage par mots-clés", 
                     help="Entrez des mots-clés pour filtrer les articles. La recherche s'applique au titre, au résumé et aux catégories arxiv.")

        placeholder_text = """Exemples :  cs.HC (terminologie arXiv)
                        q-bio.NC
                        agentic
                        education
                        deep learning"""
        
        keywords_input = st.text_area(
            "Un mot-clé par ligne:",
            value="",
            placeholder=placeholder_text,
            height=150
        )
        
        keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
        
        if keywords:
            st.info(f"🔍 {len(keywords)} mots-clés actifs: {', '.join(keywords)}")
        
        # Nombre d'articles récents
        st.subheader("Nombre d'articles")
        max_articles = st.slider("Nombre d'articles à récupérer", 100, 1000, 100, 100)

        # Bouton pour lancer la recherche
        search_button = st.button("🔍 Lancer la recherche", type="primary")
    
    # Zone principale pour l'affichage des résultats
    if search_button:
        if not selected_categories:
            st.error("Veuillez sélectionner au moins une catégorie.")
        else:
            # Afficher un message de chargement
            with st.spinner("Récupération des articles en cours..."):
                try:
                    # Configuration de la UI pour le feedback
                    progress_bar = st.progress(0)
                    status = st.empty()
                    
                    details_container = st.container()
                    col1, col2 = details_container.columns([2, 1])
                    detail_log = col1.empty()
                    stats_display = col2.empty()
                    
                    # Initialiser les logs détaillés
                    search_details = []
                    stats = {"total": 0, "filtered": 0, "batches": 0, "duplicates": 0}
                    
                    # Fonctions de mise à jour de l'interface
                    def add_log(message, level="info"):
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        icon = "🔍" if level == "info" else "✅" if level == "success" else "⚠️" if level == "warning" else "❌"
                        search_details.append(f"{icon} `{timestamp}` {message}")
                        log_text = "\n\n".join(search_details[-10:])
                        detail_log.markdown(f"### Détails de la recherche\n{log_text}")
                    
                    def update_stats():
                        stats_text = f"""
                        ### Statistiques
                        - **Articles trouvés:** {stats['total']}
                        - **Lots traités:** {stats['batches']}
                        - **Doublons ignorés:** {stats['duplicates']}
                        - **Articles filtrés:** {stats['filtered']}
                        """
                        stats_display.markdown(stats_text)
                    
                    # Callback pour les mises à jour de progression
                    def progress_callback(status_message, batch_info=None, level="info"):
                        add_log(status_message, level=level)
                        if batch_info:
                            stats["batches"] += 1
                            stats["total"] = batch_info.get("total", stats["total"])
                            stats["duplicates"] = batch_info.get("duplicates", stats["duplicates"])
                            update_stats()
                            progress_value = min(batch_info.get("total", 0) / max_articles, 0.8)
                            progress_bar.progress(progress_value)
                    
                    # Récupération des articles
                    add_log("Initialisation de la recherche...")
                    progress_bar.progress(0.1)
                    
                    start_time = time.time()
                    add_log(f"Récupération de maximum {max_articles} articles récents...")
                    
                    articles = get_latest_arxiv_articles(
                        categories=selected_categories,
                        max_articles=max_articles,
                        strict_category=strict_category,
                        callback=progress_callback
                    )
                    
                    elapsed = time.time() - start_time
                    add_log(f"{len(articles)} articles récupérés en {elapsed:.1f} secondes", level="success")
                    progress_bar.progress(0.8)
                    stats["total"] = len(articles)
                    update_stats()
                    
                    # Filtrer par mots-clés
                    if keywords and articles:
                        add_log(f"Application du filtrage par {len(keywords)} mots-clés...")
                        filtered_articles = filter_articles_by_keywords_multi(articles, keywords)
                        stats["filtered"] = len(filtered_articles)
                        update_stats()
                        add_log(f"{len(filtered_articles)} articles correspondent aux mots-clés", level="success")
                    else:
                        filtered_articles = articles
                        stats["filtered"] = len(articles)
                        update_stats()
                    
                    progress_bar.progress(1.0)
                    status.text(f"✅ Traitement terminé: {len(filtered_articles)}/{len(articles)} articles après filtrage")
                    
                    # Stocker les articles dans session_state
                    st.session_state.arxiv_articles = filtered_articles
                    
                except Exception as e:
                    st.error(f"Erreur : {e}")
    
    # Afficher les articles s'ils sont disponibles dans session_state
    if st.session_state.arxiv_articles:
        filtered_articles = st.session_state.arxiv_articles
        
        st.success(f"✅ {len(filtered_articles)} articles trouvés")
        
        # Créer deux onglets pour afficher les résultats
        tab1, tab2 = st.tabs(["Articles filtrés", "Tous les articles"])
        
        with tab1:
            display_arxiv_articles(filtered_articles, "Articles filtrés par mots-clés")
            
            # Zone de sélection d'article
            st.subheader("Sélectionner un article à traiter")
                      
            selected_index = st.number_input("Index de l'article à traiter", 
                                           min_value=0, 
                                           max_value=len(filtered_articles)-1 if filtered_articles else 0,
                                           label_visibility="visible")
            
            process_button = st.button("Traiter cet article")

            
            if len(filtered_articles) > 0:
                # Afficher les détails de l'article sélectionné UNIQUEMENT
                st.subheader("Détails de l'article sélectionné")
                
                if selected_index < len(filtered_articles):
                    article = filtered_articles[selected_index]
                    display_article_details(article)
            
            # Traiter l'article si le bouton principal est cliqué
            if process_button and len(filtered_articles) > 0:
                article = filtered_articles[selected_index]
                data, category, success = prepare_arxiv_article_data(article)
                process_extraction(data, category, success, 'arxiv_scraper')
        
        with tab2:
            # Dans l'onglet "Tous les articles", il n'y a pas de filtrage mais les mêmes données
            # que celles récupérées initialement
            display_arxiv_articles(st.session_state.arxiv_articles, "Tous les articles récupérés")

def show_reddit_scraper_page():
    """Page du scrapper Reddit"""
    st.title("Recherche sur Reddit ")

    # Bouton de retour
    if st.button("← Retour à l'accueil", key="home_from_reddit"):
        navigate_to('home')

    st.markdown("""
    Recherchez et filtrez les articles récents de Reddit.
    """)

    with st.spinner("Recupération des posts en cours..."):
        try:
            posts = get_entries_from_reddit()
            st.session_state.reddit_posts = posts
        except Exception as e:
            st.error(f"Erreur : {e}")

        if st.session_state.reddit_posts:
            reddit_posts = st.session_state.reddit_posts

            st.success(f"✅ {len(reddit_posts)} posts trouvés")

            st.subheader("Reddit Posts")

            df = pd.DataFrame([{
                "Index": idx,
                "Liens": post['links'][0],
                "Titre": post['title'],
                "Text": post['text']
            } for idx, post in enumerate(reddit_posts)])
 
            #st.dataframe(df, use_container_width=True)

            for index, row in df.iterrows():
                col1, col2 = st.columns([4,1])
                with col1:
                    st.markdown(f"**{row['Titre']}**")
                    st.text(row['Text'][:100]+"...")
                with col2:
                    if st.button("🔍 Analyser", key=row['Liens']):
                        st.session_state.selected_url = row['Liens']
                        navigate_to('regular_extraction')

def show_huggingface_scraper_page():
    """Page de scraping automatique des articles HuggingFace"""
    st.title("Recherche sur HuggingFace 🧠")

    if st.button("← Retour à l'accueil", key="home_from_huggingface"):
        navigate_to('home')

    st.markdown("""
    Retrouvez ici les dernières publications d'articles partagés sur HuggingFace Papers.
    Sélectionnez la période puis cliquez sur "Rechercher maintenant" pour récupérer les articles.
    """)

    mode = st.radio("Choisissez la périodicité :", ["Hebdomadaire", "Mensuel"], horizontal=True)

    selected_year = st.selectbox("Année :", list(range(2025, 2019, -1)), index=0)

    if mode == "Hebdomadaire":
        selected_week = st.number_input("Semaine de l'année :", min_value=1, max_value=52, value=12, step=1)
        main_page_id = f"week/{selected_year}-W{selected_week:02d}"
        start_of_week = date.fromisocalendar(selected_year, selected_week, 1)  # Monday
        end_of_week = start_of_week + timedelta(days=6)

        st.caption(f"📅 Du {start_of_week.strftime('%d %B %Y')} au {end_of_week.strftime('%d %B %Y')}")
    else:
        months = {
            "Janvier": "01", "Février": "02", "Mars": "03", "Avril": "04",
            "Mai": "05", "Juin": "06", "Juillet": "07", "Août": "08",
            "Septembre": "09", "Octobre": "10", "Novembre": "11", "Décembre": "12"
        }
        month_names = list(months.keys())
        selected_month_name = st.selectbox("Mois :", month_names, index=2)
        selected_month = months[selected_month_name]
        main_page_id = f"month/{selected_year}-{selected_month}"

    search_button = st.button("🔍 Rechercher maintenant")

    if search_button:
        with st.spinner(f"Récupération des articles pour {main_page_id}..."):
            try:
                posts = get_entries_from_huggingface(main_page_id=main_page_id)
                st.session_state.huggingface_posts = posts
            except Exception as e:
                st.error(f"Erreur : {e}")
                return

    if st.session_state.get("huggingface_posts"):
        hf_posts = st.session_state.huggingface_posts

        st.success(f"✅ {len(hf_posts)} articles HuggingFace trouvés")
        st.subheader("Articles HuggingFace")

        table_data = []
        for idx, post in enumerate(hf_posts):
            title = post.get('title', f"Paper {idx}")
            text = post.get('content', '')
            link = post.get('links', [''])[0]

            table_data.append({
                "Index": idx,
                "Lien": link,
                "Titre": title,
                "Texte": text
            })

        df = pd.DataFrame(table_data)

        for index, row in df.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{row['Titre']}**")
                st.text(row['Texte'][:100] + "...")
            with col2:
                if row['Lien']:
                    if st.button("🔍 Analyser", key="hf_" + row['Lien']):
                        st.session_state.selected_url = row['Lien']
                        navigate_to('regular_extraction')
                else:
                    st.markdown("🔗 Lien manquant")
                                
def process_data_pipeline():
    """
    Affiche l'interface UNIFIÉE de traitement pour les données extraites,
    quelle que soit leur source (URL ou ArXiv)
    """
    st.title("Traitement des données")
    
    # Bouton de retour adaptatif selon la source
    source = st.session_state.extracted_data.get("source", "unknown")
    if source == "arxiv":
        if st.button("← Retour à la recherche ArXiv", key="back_to_source"):
            if "extracted_data" in st.session_state:
                del st.session_state.extracted_data

            if "summary" in st.session_state:
                del st.session_state.summary
            
            if "review" in st.session_state:
                del st.session_state.review
            
            if "rouge_scores" in st.session_state:
                del st.session_state.rouge_scores

            navigate_to('arxiv_scraper')
    else:
        if st.button("← Retour à l'extraction par URL", key="back_to_source"):
            if "extracted_data" in st.session_state:
                del st.session_state.extracted_data

            if "summary" in st.session_state:
                del st.session_state.summary
            
            if "review" in st.session_state:
                del st.session_state.review
            
            if "rouge_scores" in st.session_state:
                del st.session_state.rouge_scores
                
            navigate_to('regular_extraction')
    
    # Afficher les données extraites
    if "extracted_data" in st.session_state:
        data = st.session_state.extracted_data
        st.markdown(f"## {data['title']}")
        
        # Afficher toutes les métadonnées disponibles
        metadata_fields = [
            ("authors", "Auteurs", lambda x: ', '.join(x) if isinstance(x, list) else x),
            ("url", "Source", lambda x: f"[{'ArXiv' if source=='arxiv' else 'Source'}]({x})"),
            ("category", "Catégorie", lambda x: x),
            ("date", "Date", lambda x: x)
        ]
        
        for field, label, formatter in metadata_fields:
            if field in data and data[field]:
                st.markdown(f"**{label}:** {formatter(data[field])}")
        
        # Afficher le contenu
        st.markdown("### Contenu")
        with st.expander("Voir le contenu complet", expanded=False):
            st.write(data.get('content', 'Aucun contenu disponible'))
        
        # Informations de catégorie
        st.markdown("### Classification")
        with st.container():
            if "extracted_category" in st.session_state:
                st.success(f"**Catégorie détectée :** {st.session_state.extracted_category}")
            else:
                st.warning("Aucune catégorie détectée")
        
        # Section de résumé - Action commune quelle que soit la source
        st.markdown("## Interprétation")
        if st.button("Résumer le contenu 📝"):
            generate_content_summary()
        
        # Afficher le résumé s'il est disponible
        if "summary" in st.session_state:
            st.markdown("### Résumé Généré")
            st.write(st.session_state.summary)
            st.write(f"**Prix du résumé** 💸: {st.session_state.summary_price}$")
    
            # Section d'évaluation - Actions communes quelle que soit la source
            st.markdown("## Evaluation et Critique")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Critiquer le résumé 💯"):
                    evaluate_summary_with_critique()
    
                if "review" in st.session_state:
                    st.markdown("### Critique du résumé :")
                    st.write(st.session_state.review)
                
            with col2:
                if st.button("Évaluer le Résumé avec Rouge 🧮"):
                    calculate_rouge_metrics()
            
                if "rouge_scores" in st.session_state:
                    st.markdown("### Scores Rouge :")
                    st.write("**Rouge-1 Précision :** {:.2f}".format(st.session_state.rouge_scores["rouge1_precision"]))
                    st.write("**Rouge-2 Précision :** {:.2f}".format(st.session_state.rouge_scores["rouge2_precision"]))
                    st.write("**Rouge-L Précision :** {:.2f}".format(st.session_state.rouge_scores["rougeL_precision"]))
    else:
        st.error("Aucune donnée n'est disponible. Veuillez retourner à l'extraction.")

def show_footer():
    """Affiche le pied de page commun"""
    st.markdown("---")
    
    # Ajouter le bouton de réinitialisation avant le footer
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🏠 Retour à l'accueil (réinitialiser tout)", use_container_width=True):
            reset_and_go_home()
    
    st.markdown(
        """
        © 2024 Arij BEN RHOUMA, Antoine CASTEL, Arthur VOGELS - Projet de fin d'étude CentraleSupélec X ILLUIN Technology 🤖.
        """
    )

# Application principale - routage basé sur l'état de session
def main():
    # Router: affiche différentes pages selon l'état de session
    router = {
        'home': show_home_page,
        'regular_extraction': show_regular_extraction_page,
        'arxiv_scraper': show_arxiv_scraper_page,
        'process_data': process_data_pipeline,
        'reddit_scraper': show_reddit_scraper_page,
        'huggingface_scraper': show_huggingface_scraper_page,
    }
    
    # Afficher la page actuelle ou par défaut la page d'accueil
    current_page = st.session_state.page
    page_function = router.get(current_page, show_home_page)
    page_function()
    
    # Toujours afficher le footer
    show_footer()

# Point d'entrée
if __name__ == "__main__":
    main()
