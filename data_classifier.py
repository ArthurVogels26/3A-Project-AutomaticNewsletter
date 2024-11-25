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

        :param data: Dictionnaire contenant les métadonnées extraites de Hugging Face
        :return: Chaîne indiquant "dataset", "model" ou "unknown"
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

        :param data: Dictionnaire des métadonnées
        :return: Booléen indiquant si les données sont un dataset
        """
        return 'datasetId' in data

    @staticmethod
    def is_model(data):
        """
        Vérifie si les données correspondent à un modèle.

        :param data: Dictionnaire des métadonnées
        :return: Booléen indiquant si les données sont un modèle
        """
        return 'modelId' in data

    @staticmethod
    def classify(data):
        """
        Classifie génériquement les données extraites.

        :param data: Dictionnaire contenant les métadonnées extraites
        :return: Chaîne indiquant le type de données ("dataset", "model", "unknown")
        """
        if DataClassifier.is_dataset(data):
            return "dataset"
        elif DataClassifier.is_model(data):
            return "model"
        else:
            return "unknown"
