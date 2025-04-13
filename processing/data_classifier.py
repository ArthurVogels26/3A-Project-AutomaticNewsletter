class DataClassifier:
    """
    Classe pour classifier les données extraites en fonction de leur type :
    - Dataset
    - Modèle
    """

    @staticmethod
    def classify_huggingface_data(data):
        """
        Classifie les données Hugging Face comme étant un modèle ou un dataset.
        """
        if 'datasetId' in data:
            return "dataset"
        elif 'modelId' in data:
            return "model"
        else:
            return "unknown"

    @staticmethod
    def is_dataset(data):
        """
        Vérifie si les données correspondent à un dataset.

        """
        if data.get('source_type') == "huggingface_dataset" :
            return True
        else:
            # METTRE METHODE DE CLASSIFICATION
            return False

    @staticmethod
    def is_model(data):
        """
        Vérifie si les données correspondent à un modèle.

        """
        if data.get('source_type') == "huggingface_model" :
            return True
        else:
            # METTRE METHODE DE CLASSIFICATION
            return False

    @staticmethod
    def classify(data):
        """
        Classifie génériquement les données extraites.
        """
        if DataClassifier.is_dataset(data):
            return "dataset"
        elif DataClassifier.is_model(data):
            return "model"
        else:
            return "unknown"
