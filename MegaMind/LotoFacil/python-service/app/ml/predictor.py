"""
LotofacilPredictor — Módulo de Machine Learning.

Implementa:
  • Random Forest Classifier  → prever quais dezenas têm maior chance de sair
  • KMeans Clustering          → agrupar dezenas que aparecem juntas

Feature Engineering:
  - Frequência acumulada
  - Atraso (quantos concursos desde a última aparição)
  - Tendência (diferença de frequência entre janelas recentes)
  - Paridade (par/ímpar)
  - Faixa (baixa 1-8 / média 9-17 / alta 18-25)
"""
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler


class LotofacilPredictor:
    """Motor de Machine Learning para previsão de padrões da Lotofácil."""

    def __init__(self):
        self.model: RandomForestClassifier | None = None
        self.scaler = StandardScaler()
        self.acuracia: float = 0.0
        self.feature_names: list[str] = []
        self.feature_importances: list[dict] = []

    # ══════════════════════════════════════════════════════════════
    #  FEATURE ENGINEERING
    # ══════════════════════════════════════════════════════════════
    def _build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Constrói features para cada (concurso, dezena).

        Para cada concurso i e dezena d, olhamos os concursos
        ANTERIORES a i (i+1 em diante no DataFrame, que está em
        ordem decrescente de concurso) para extrair:
          - freq_acum   : frequência acumulada nos últimos N jogos
          - atraso       : quantos concursos desde a última vez que saiu
          - tendencia    : freq nos últimos 5 - freq nos 5 anteriores
          - paridade     : 1 se par, 0 se ímpar
          - faixa        : 0=baixa (1-8), 1=média (9-17), 2=alta (18-25)
          - target       : 1 se a dezena saiu neste concurso
        """
        records: list[dict] = []
        dezenas_col = df["Dezenas"].tolist()
        n = len(dezenas_col)

        for i in range(n - 1):  # não usar o último (sem histórico anterior suficiente)
            sorteio_atual = set(dezenas_col[i])

            # Janela de histórico: concursos após o atual (mais antigos)
            historico = dezenas_col[i + 1: min(i + 51, n)]
            if len(historico) < 5:
                continue

            # Contagem de frequência
            todas = [d for row in historico for d in row]
            freq_counter = Counter(todas)
            total_jogos = len(historico)

            # Frequência nas duas janelas para tendência
            janela_recente = historico[:5]
            janela_anterior = historico[5:10] if len(historico) >= 10 else historico[5:]
            freq_recente = Counter([d for row in janela_recente for d in row])
            freq_anterior = Counter([d for row in janela_anterior for d in row]) if janela_anterior else Counter()

            for dezena in range(1, 26):
                # Atraso: em quantos concursos consecutivos anteriores a dezena NÃO saiu
                atraso = 0
                for h_row in historico:
                    if dezena in h_row:
                        break
                    atraso += 1

                freq_acum = freq_counter.get(dezena, 0) / total_jogos
                tend = freq_recente.get(dezena, 0) - freq_anterior.get(dezena, 0)

                records.append({
                    "freq_acum": freq_acum,
                    "atraso": atraso,
                    "tendencia": tend,
                    "paridade": 1 if dezena % 2 == 0 else 0,
                    "faixa": 0 if dezena <= 8 else (1 if dezena <= 17 else 2),
                    "dezena": dezena,
                    "target": 1 if dezena in sorteio_atual else 0,
                })

        features_df = pd.DataFrame(records)
        self.feature_names = ["freq_acum", "atraso", "tendencia", "paridade", "faixa"]
        return features_df

    # ══════════════════════════════════════════════════════════════
    #  TREINAMENTO — RANDOM FOREST
    # ══════════════════════════════════════════════════════════════
    def treinar(self, df: pd.DataFrame) -> dict:
        """
        Treina um Random Forest para prever se cada dezena sairá.
        Retorna métricas de treinamento.
        """
        features_df = self._build_features(df)

        if features_df.empty:
            raise ValueError("Dados insuficientes para treinamento")

        X = features_df[self.feature_names].values
        y = features_df["target"].values

        # Escalar features
        X_scaled = self.scaler.fit_transform(X)

        # Treinar modelo
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight="balanced",
            n_jobs=-1,
        )
        self.model.fit(X_scaled, y)

        # Cross-validation
        scores = cross_val_score(self.model, X_scaled, y, cv=5, scoring="accuracy")
        self.acuracia = float(np.mean(scores))

        # Feature importances
        self.feature_importances = [
            {"feature": name, "importancia": float(imp)}
            for name, imp in zip(self.feature_names, self.model.feature_importances_)
        ]
        self.feature_importances.sort(key=lambda x: x["importancia"], reverse=True)

        return {
            "acuracia_media": self.acuracia,
            "acuracia_std": float(np.std(scores)),
            "n_amostras": len(X),
            "features_importancia": self.feature_importances,
        }

    # ══════════════════════════════════════════════════════════════
    #  PREVISÃO
    # ══════════════════════════════════════════════════════════════
    def prever_proximas(self, df: pd.DataFrame, top_n: int = 15) -> dict:
        """
        Prevê a probabilidade de cada dezena (1-25) sair no PRÓXIMO sorteio.
        Usa os dados mais recentes como base de features.
        """
        if self.model is None:
            self.treinar(df)

        # Construir features para o "próximo" sorteio
        dezenas_col = df["Dezenas"].tolist()
        historico = dezenas_col[:50]

        if len(historico) < 5:
            raise ValueError("Histórico insuficiente para previsão")

        todas = [d for row in historico for d in row]
        freq_counter = Counter(todas)
        total_jogos = len(historico)

        janela_recente = historico[:5]
        janela_anterior = historico[5:10] if len(historico) >= 10 else historico[5:]
        freq_recente = Counter([d for row in janela_recente for d in row])
        freq_anterior = Counter([d for row in janela_anterior for d in row]) if janela_anterior else Counter()

        records = []
        for dezena in range(1, 26):
            atraso = 0
            for h_row in historico:
                if dezena in h_row:
                    break
                atraso += 1

            records.append({
                "freq_acum": freq_counter.get(dezena, 0) / total_jogos,
                "atraso": atraso,
                "tendencia": freq_recente.get(dezena, 0) - freq_anterior.get(dezena, 0),
                "paridade": 1 if dezena % 2 == 0 else 0,
                "faixa": 0 if dezena <= 8 else (1 if dezena <= 17 else 2),
                "dezena": dezena,
            })

        pred_df = pd.DataFrame(records)
        X_pred = self.scaler.transform(pred_df[self.feature_names].values)

        # Probabilidades de classe positiva (dezena sai)
        probas = self.model.predict_proba(X_pred)[:, 1]

        # Criar ranking
        scores = []
        for idx, row in pred_df.iterrows():
            scores.append({
                "dezena": int(row["dezena"]),
                "probabilidade": round(float(probas[idx]), 4),
            })

        scores.sort(key=lambda x: x["probabilidade"], reverse=True)

        for rank, s in enumerate(scores, 1):
            s["ranking"] = rank

        dezenas_recomendadas = [s["dezena"] for s in scores[:top_n]]

        return {
            "dezenas_recomendadas": sorted(dezenas_recomendadas),
            "scores": scores,
            "modelo": "RandomForestClassifier",
            "acuracia_treino": self.acuracia,
            "features_importancia": self.feature_importances,
        }

    # ══════════════════════════════════════════════════════════════
    #  CLUSTERING — KMEANS
    # ══════════════════════════════════════════════════════════════
    def identificar_clusters(self, df: pd.DataFrame, n_clusters: int = 4) -> dict:
        """
        Agrupa as 25 dezenas em clusters baseados em co-ocorrência.
        """
        # Matriz de co-ocorrência 25x25
        coocorrencia = np.zeros((25, 25))

        for dezenas in df["Dezenas"]:
            for i, d1 in enumerate(dezenas):
                for d2 in dezenas[i + 1:]:
                    coocorrencia[d1 - 1][d2 - 1] += 1
                    coocorrencia[d2 - 1][d1 - 1] += 1

        # Normalizar
        scaler = StandardScaler()
        X = scaler.fit_transform(coocorrencia)

        # KMeans
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        clusters = [
            {"dezena": d + 1, "cluster": int(labels[d])}
            for d in range(25)
        ]

        # Descrição de cada cluster
        descricao = []
        for c in range(n_clusters):
            membros = [item["dezena"] for item in clusters if item["cluster"] == c]
            descricao.append(
                f"Cluster {c + 1}: dezenas {membros} — "
                f"{len(membros)} membros, "
                f"média={np.mean(membros):.1f}"
            )

        return {
            "clusters": clusters,
            "n_clusters": n_clusters,
            "descricao": descricao,
        }
