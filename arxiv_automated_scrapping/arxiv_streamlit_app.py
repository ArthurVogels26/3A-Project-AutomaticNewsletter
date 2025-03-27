import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, timezone, timedelta
import os
from arxiv_latest_scrapping import (
    get_latest_arxiv_articles,
    filter_articles_by_keywords_multi
)

st.set_page_config(
    page_title="ArXiv IA Explorer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📚 ArXiv IA Explorer")
    st.markdown("""
    Cette application vous permet de récupérer et d'explorer les derniers articles d'ArXiv 
    publié.
    """)
    
    # Sidebar pour les paramètres
    with st.sidebar:
        st.header("Paramètres de recherche")
        
        # Mode de filtrage par catégorie (placé avant les catégories)
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
        
        # En mode strict, utiliser un radio button pour sélectionner une seule catégorie
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
            # En mode inclusif, garder les checkboxes pour sélectionner plusieurs catégories
            selected_categories = []
            for name, cat_id in categories.items():
                if st.checkbox(name, value=False, key=f"cat_{cat_id}"):
                    selected_categories.append(cat_id)
               
        # Mots-clés pour filtrer (avec placeholder)
        st.subheader("Filtrage par mots-clés", 
                     help="Entrez des mots-clés pour filtrer les articles. La recherche s'applique au titre, au résumé et aux catégories arxiv.")

        
        placeholder_text = """Exemples :  cs.HC (terminologie arXiv)
                        q-bio.NC
                        agentic
                        industry
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
        st.subheader("Nombre d'articles",
                     help="Le mode strict peut limiter le nombre d'articles récupérés.")
        max_articles = st.slider("Nombre d'articles les plus récents à récupérer", 100, 1000, 100, 100)

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
                    # Récupérer les articles
                    progress_bar = st.progress(0)
                    status = st.empty()
                    
                    # Zone d'affichage des détails avec 2 colonnes
                    details_container = st.container()
                    col1, col2 = details_container.columns([2, 1])
                    detail_log = col1.empty()
                    stats_display = col2.empty()
                    
                    # Initialiser les logs détaillés
                    search_details = []
                    stats = {"total": 0, "filtered": 0, "batches": 0, "duplicates": 0}
                    
                    # Fonction pour ajouter des logs détaillés
                    def add_log(message, level="info"):
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        icon = "🔍" if level == "info" else "✅" if level == "success" else "⚠️" if level == "warning" else "❌"
                        search_details.append(f"{icon} `{timestamp}` {message}")
                        # Limiter à 15 derniers messages
                        log_text = "\n\n".join(search_details[-10:])
                        detail_log.markdown(f"### Détails de la recherche\n{log_text}")
                    
                    # Fonction pour mettre à jour les statistiques
                    def update_stats():
                        stats_text = f"""
                        ### Statistiques
                        - **Articles trouvés:** {stats['total']}
                        - **Lots traités:** {stats['batches']}
                        - **Doublons ignorés:** {stats['duplicates']}
                        - **Articles filtrés:** {stats['filtered']}
                        """
                        stats_display.markdown(stats_text)
                    
                    # Récupération des articles
                    add_log("Initialisation de la recherche d'articles ArXiv...")
                    progress_bar.progress(0.1)
                    
                    # Utiliser la nouvelle fonction pour récupérer les articles les plus récents
                    start_time = time.time()
                    add_log(f"Récupération de maximum {max_articles} articles récents... Mode de filtrage : {'Strict' if strict_category else 'Inclusif'}")
                    
                    # Callback pour recevoir des mises à jour de progression
                    def progress_callback(status_message, batch_info=None, level="info"):
                        add_log(status_message, level=level)
                        if batch_info:
                            stats["batches"] += 1
                            stats["total"] = batch_info.get("total", stats["total"])
                            stats["duplicates"] = batch_info.get("duplicates", stats["duplicates"])
                            update_stats()
                            
                            # Mettre à jour la barre de progression
                            progress_value = min(batch_info.get("total", 0) / max_articles, 0.8)
                            progress_bar.progress(progress_value)
                    
                    articles = get_latest_arxiv_articles(
                        categories=selected_categories,
                        max_articles=max_articles,
                        strict_category=strict_category,
                        callback=progress_callback  # Nouveau paramètre pour les mises à jour
                    )
                    
                    elapsed = time.time() - start_time
                    add_log(f"{len(articles)} articles récupérés en {elapsed:.1f} secondes", level="success")
                    progress_bar.progress(0.8)
                    stats["total"] = len(articles)
                    update_stats()
                    
                    # Filtrer par mots-clés (sur tous les champs pertinents)
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
                    
                    # Préparer les données pour le téléchargement
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    all_articles_file = f"tous_articles_ia_{timestamp}.json"
                    filtered_articles_file = f"articles_ia_filtres_{timestamp}.json"
                    
                    # Afficher les statistiques
                    st.success(f"✅ Récupération terminée ! {len(articles)} articles trouvés, {len(filtered_articles)} après filtrage.")
                    
                    # Créer des onglets pour afficher les résultats
                    tab1, tab2 = st.tabs(["Articles filtrés", "Tous les articles"])
                    
                    with tab1:
                        display_articles(filtered_articles, filtered_articles_file)
                    
                    with tab2:
                        display_articles(articles, all_articles_file)
                    
                except Exception as e:
                    st.error(f"Erreur : {e}")
    else:
        # Afficher une image ou un message d'accueil
        st.info("👈 Configurez les paramètres de recherche et cliquez sur 'Lancer la recherche'")

def display_articles(articles, json_file):
    """Affiche les articles sous forme de tableau et de cartes"""
    if not articles:
        st.warning("Aucun article trouvé.")
        return
    
    # Créer un DataFrame pour afficher les articles
    df = pd.DataFrame([{
        "Titre": article["title"],
        "Auteurs": ", ".join(article["authors"]),
        "Date": format_date(article["published_date"]),
        "Catégorie": article["category"],
        "Toutes catégories": ", ".join(article.get("all_categories", [article["category"]])),
        "Résumé": article["summary"][:150] + "..." if len(article["summary"]) > 150 else article["summary"],
        "Lien": article["link"]
    } for article in articles])
    
    # Exporter les données à la demande
    json_str = json.dumps(articles, ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 Télécharger en JSON",
        data=json_str,
        file_name=json_file,
        mime="application/json"
    )
    
    # Afficher le tableau
    st.dataframe(df, use_container_width=True)
    
    # Afficher les cartes d'articles individuels
    st.subheader("Articles détaillés")
    
    # Diviser en colonnes pour afficher plusieurs cartes par ligne
    cols = st.columns(2)
    
    # Afficher les 10 premiers articles sous forme de cartes détaillées
    for i, article in enumerate(articles[:10]):
        with cols[i % 2]:
            with st.expander(f"{i+1}. {article['title']}", expanded=False):
                st.markdown(f"**Auteurs:** {', '.join(article['authors'])}")
                st.markdown(f"**Date:** {format_date(article['published_date'])}")
                st.markdown(f"**Catégorie:** {article['category']}")
                st.markdown(f"**Lien:** [{article['link']}]({article['link']})")
                st.markdown("**Résumé:**")
                st.markdown(article['summary'])
                st.markdown("---")

def format_date(date_str):
    """Formate la date en format lisible"""
    if not date_str:
        return "Date inconnue"
    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date.strftime("%d/%m/%Y")
    except:
        return date_str

if __name__ == "__main__":
    main()
