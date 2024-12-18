from rouge_score import rouge_scorer
import data_extractor as d_ex
from summarizerAgent import generate_summary

def evaluate_summary_with_original(generated_summary: str, original_content: str):

    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(original_content, generated_summary)
    
    results = {
        "rouge1_precision": scores["rouge1"].precision,
        "rouge2_precision": scores["rouge2"].precision,
        "rougeL_precision": scores["rougeL"].precision,
    }
    return results

if __name__ == "__main__":
    extractor = d_ex.DataExtractor()
    original_content = extractor.extract("https://arxiv.org/pdf/1611.07004").to_dict()
    generated_summary = generate_summary(original_content)
    rouge_results = evaluate_summary_with_original(generated_summary, original_content["content"])

    print(f"ROUGE Evaluation Results: {rouge_results}")
