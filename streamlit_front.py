import streamlit as st
import data_extractor as d_ex
import data_classifier as d_c

# Configuration de la page
st.set_page_config(
    page_title="Newsletter Generator",
    page_icon="todo",
    layout="centered"
)

# Titre principal
st.title("Générateur de Newsletter Automatique :wave:")

# Description
st.write("""
Bienvenue sur cette application de démonstration. Ici, vous pouvez entrer un lien ou un identifiant (arXiv, GitHub, Hugging Face, ou un blog) 
et l'outil extraira automatiquement les métadonnées et le contenu pertinent pour générer une newsletter.
""")

# Entrée utilisateur
url_or_id = st.text_input("Entrez l'URL ou l'identifiant de la ressource :", placeholder="Exemple : https://arxiv.org/abs/1234.56789", )

# Gestion de l'option disable du bouton pour le run
if 'extract_button' in st.session_state and st.session_state.extract_button == True:
    st.session_state.running = True
else:
    st.session_state.running = False

# Bouton pour lancer l'extraction
if st.button("Extraire les données 🚀", disabled=st.session_state.running, key="extract_button"):
    if url_or_id.strip() == "":
        st.warning("Veuillez entrer un lien ou un identifiant valide.")
    else:
        extractor = d_ex.DataExtractor()
        classifier = d_c.DataClassifier()
        try:
            with st.spinner("Extraction en cours..."):

                # Appel des fonctions
                data = extractor.extract(url_or_id)
                category = classifier.classify(data)

                # Stockage des données extraites dans la session web
                st.session_state.extracted_data = data
                st.session_state.extracted_category = category

        except Exception as e:
                st.error(f"Une erreur s'est produite lors de l'extraction : {e}")
    # Rendre le bouton a nouveau cliquable
    st.rerun()

if "extracted_data" in st.session_state:
    st.success("Extraction réussie ! Voici les données récupérées :")
    with st.container(height=600):
        st.json(st.session_state.extracted_data)

    st.markdown("### Résultat de Classification :")
    with st.container():
        st.write(f"**Catégorie détectée :** {st.session_state.extracted_category.capitalize()}")
        if st.session_state.extracted_category != "dataset" and st.session_state.extracted_category != "model":
            st.warning("Type de données non reconnu. Veuillez vérifier les métadonnées.")

# Footer
st.markdown("---")
st.markdown(
    """
    © 2024 Arij BEN RHOUMA, Antoine CASTEL, Arthur VOGELS  - Projet de fin d'étude CentraleSupélec X ILLUIN Technology 🤖.
    """
)
