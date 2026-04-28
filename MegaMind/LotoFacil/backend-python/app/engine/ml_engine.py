from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
import numpy as np
import logging

logger = logging.getLogger(__name__)

class XGBMLEngine:
    """
    Motor de Machine Learning utilizando XGBoost para identificação de padrões
    em sorteios da Lotofácil.
    """

    def __init__(self, n_estimators=200, learning_rate=0.05, max_depth=6):
        self.model = XGBClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        self.is_trained = False

    def train(self, X: np.ndarray, y: np.ndarray):
        """
        Treina o modelo XGBoost.
        X deve conter as features produzidas pelo FeatureEngineer.
        """
        logger.info("Starting XGBoost training...")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        self.is_trained = True
        
        score = self.model.score(X_test, y_test)
        logger.info(f"XGBoost training complete. Accuracy: {score:.4f}")
        return score

    def predict_probabilities(self, X: np.ndarray):
        """
        Prediz a probabilidade de cada número (1-25) ser sorteado.
        """
        if not self.is_trained:
            raise RuntimeError("Model is not trained yet")
        return self.model.predict_proba(X)[:, 1]
