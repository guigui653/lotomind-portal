package com.lotofacil.service;

import com.fasterxml.jackson.databind.JsonNode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Map;

/**
 * Service que faz chamadas HTTP ao microsserviço Python (FastAPI).
 * Atua como proxy/orquestrador entre o Java e o Python.
 */
@Service
public class PythonClientService {

    private static final Logger log = LoggerFactory.getLogger(PythonClientService.class);
    private final WebClient webClient;

    public PythonClientService(@Value("${python.service.base-url}") String baseUrl) {
        this.webClient = WebClient.builder()
                .baseUrl(baseUrl)
                .defaultHeader("Content-Type", "application/json")
                .build();
    }

    // ── Dashboard ────────────────────────────────────────────────
    public JsonNode getDashboard(int qtd) {
        log.debug("Requisitando dashboard (qtd={})", qtd);
        return get("/analysis/dashboard?qtd=" + qtd);
    }

    // ── Frequências ──────────────────────────────────────────────
    public JsonNode getFrequencies(int qtd) {
        return get("/analysis/frequencies?qtd=" + qtd);
    }

    // ── Heatmap ──────────────────────────────────────────────────
    public JsonNode getHeatmap(int qtd, int blocos) {
        return get("/analysis/heatmap?qtd=" + qtd + "&blocos=" + blocos);
    }

    // ── Gerar Jogo ───────────────────────────────────────────────
    public JsonNode generateGame(String estrategia, int qtdConcursos) {
        Map<String, Object> body = Map.of(
                "estrategia", estrategia,
                "qtd_concursos", qtdConcursos);
        return post("/games/generate", body);
    }

    // ── Gerar Elite ──────────────────────────────────────────────
    public JsonNode generateElite(String melhorJogoNome, int qtdConcursos) {
        Map<String, Object> body = Map.of(
                "melhor_jogo_nome", melhorJogoNome,
                "qtd_concursos", qtdConcursos);
        return post("/games/elite", body);
    }

    // ── Backtesting ──────────────────────────────────────────────
    public JsonNode backtest(java.util.List<Integer> jogo, int qtdConcursos) {
        Map<String, Object> body = Map.of(
                "jogo", jogo,
                "qtd_concursos", qtdConcursos);
        return post("/games/backtest", body);
    }

    // ── Arsenal ──────────────────────────────────────────────────
    public JsonNode getArsenal() {
        return get("/games/arsenal");
    }

    public JsonNode simulateArsenal(int qtd) {
        return get("/games/arsenal/simulate?qtd=" + qtd);
    }

    // ── ML — Previsões ───────────────────────────────────────────
    public JsonNode predict(int qtdConcursos, int topN) {
        Map<String, Object> body = Map.of(
                "qtd_concursos", qtdConcursos,
                "top_n", topN);
        return post("/ml/predict", body);
    }

    // ── ML — Clusters ────────────────────────────────────────────
    public JsonNode getClusters(int qtd, int nClusters) {
        return post("/ml/clusters?qtd=" + qtd + "&n_clusters=" + nClusters, Map.of());
    }

    // ══════════════════════════════════════════════════════════════
    // HTTP Helpers
    // ══════════════════════════════════════════════════════════════
    private JsonNode get(String uri) {
        try {
            return webClient.get()
                    .uri(uri)
                    .retrieve()
                    .bodyToMono(JsonNode.class)
                    .timeout(Duration.ofSeconds(60))
                    .block();
        } catch (Exception e) {
            log.error("Erro GET {}: {}", uri, e.getMessage());
            throw new RuntimeException("Falha ao comunicar com serviço Python: " + e.getMessage());
        }
    }

    private JsonNode post(String uri, Object body) {
        try {
            return webClient.post()
                    .uri(uri)
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(JsonNode.class)
                    .timeout(Duration.ofSeconds(60))
                    .block();
        } catch (Exception e) {
            log.error("Erro POST {}: {}", uri, e.getMessage());
            throw new RuntimeException("Falha ao comunicar com serviço Python: " + e.getMessage());
        }
    }
}
