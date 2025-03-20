import os
import pandas as pd
import data_extractor as d_ex
import data_classifier as d_c
from summarizerAgent import generate_summary, classify_document
from evaluate_rouge import evaluate_summary_with_original


input_file = "AI takeaways benchmark.csv"
calculate_rouge = True  # Set to True to compute ROUGE scores

if os.path.exists(input_file):
    df = pd.read_csv(input_file)
else:
    raise FileNotFoundError(f"Fichier introuvable : {input_file}")

# We assume that "Take-away AI" being empty means the row needs processing
df_to_process = df[df["Take-away AI"].isna() | df["Take-away AI"].eq("")]

if df_to_process.empty:
    print("Aucun nouveau document à traiter.")
else:
    print(f"{len(df_to_process)} documents à traiter...")

extractor = d_ex.DataExtractor()
classifier = d_c.DataClassifier()

for index, row in df_to_process.iterrows():
    try:
        url_or_id = row["Link"]
        
        print(f"Traitement du document : {url_or_id}")

        data = extractor.extract(url_or_id).to_dict()

        category_ai, _ = classify_document(data)
        print(f"Catégorie détectée (AI) : {category_ai}")

        take_away_ai, _ = generate_summary(data)
        print(f"Take-away AI généré.")

        df.at[index, "Category AI"] = category_ai
        df.at[index, "Status"] = "Processed"
        df.at[index, "Take-away AI"] = take_away_ai

    except Exception as e:
        print(f"Erreur lors du traitement de {url_or_id} : {e}")
        df.at[index, "Status"] = f"Erreur: {e}"
    
#Compute ROUGE Scores
if calculate_rouge:
    print("🔢 Vérification des entrées pour ROUGE...")

    df_to_evaluate = df[
        (df["rouge1 precision"].isna() | df["rouge1 precision"].eq("")) & 
        (~df["Take-away AI"].isna()) & df["Take-away AI"].ne("")
    ]

    if df_to_evaluate.empty:
        print("Aucun score ROUGE à calculer.")
    else:
        print(f"{len(df_to_evaluate)} entrées nécessitent un score ROUGE.")

        for index, row in df_to_evaluate.iterrows():
            if pd.isna(row["Take-away AI"]) or pd.isna(row["Take-away (Illuin)"]):
                continue 
            
            rouge_scores = evaluate_summary_with_original(row["Take-away AI"], row["Take-away (Illuin)"])
            
            df.at[index, "rouge1 precision"] = round(float(rouge_scores["rouge1_precision"]), 4)
            df.at[index, "rouge2 precision"] = round(float(rouge_scores["rouge2_precision"]), 4)
            df.at[index, "rougeL precision"] = round(float(rouge_scores["rougeL_precision"]), 4)

        print("✅ ROUGE scores calculés et ajoutés au fichier.")

# Save the Updated File
df.to_csv(input_file, index=False)
print("✅ Mise à jour terminée ! Fichier sauvegardé.")