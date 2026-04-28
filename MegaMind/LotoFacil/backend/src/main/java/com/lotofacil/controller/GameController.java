package com.lotofacil.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.lotofacil.dto.BacktestRequest;
import com.lotofacil.dto.GameRequest;
import com.lotofacil.service.PythonClientService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * Controller de Jogos — Geração, Validação, Backtesting e Arsenal.
 * Requer autenticação JWT.
 */
@RestController
@RequestMapping("/api/games")
@CrossOrigin(origins = { "http://localhost:3000", "http://127.0.0.1:3000" })
public class GameController {

    private static final Logger log = LoggerFactory.getLogger(GameController.class);
    private final PythonClientService pythonClient;

    public GameController(PythonClientService pythonClient) {
        this.pythonClient = pythonClient;
    }

    /**
     * POST /api/games/generate
     * Gera um jogo validado com a estratégia especificada.
     */
    @PostMapping("/generate")
    public ResponseEntity<JsonNode> generateGame(@RequestBody GameRequest request) {
        log.info("POST /api/games/generate estrategia={}", request.estrategia());
        JsonNode result = pythonClient.generateGame(request.estrategia(), request.qtdConcursos());
        return ResponseEntity.ok(result);
    }

    /**
     * POST /api/games/elite
     * Gera 4 jogos elite com o sistema MESTRE.
     */
    @PostMapping("/elite")
    public ResponseEntity<JsonNode> generateElite(@RequestBody GameRequest request) {
        log.info("POST /api/games/elite melhorJogo={}", request.melhorJogoNome());
        String nome = request.melhorJogoNome() != null ? request.melhorJogoNome() : "Jogo 1 (Estatístico)";
        JsonNode result = pythonClient.generateElite(nome, request.qtdConcursos());
        return ResponseEntity.ok(result);
    }

    /**
     * POST /api/games/backtest
     * Simula backtesting de um jogo.
     */
    @PostMapping("/backtest")
    public ResponseEntity<JsonNode> backtest(@RequestBody BacktestRequest request) {
        log.info("POST /api/games/backtest jogo={}", request.jogo());
        JsonNode result = pythonClient.backtest(request.jogo(), request.qtdConcursos());
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/games/arsenal
     * Retorna os 8 jogos do arsenal.
     */
    @GetMapping("/arsenal")
    public ResponseEntity<JsonNode> getArsenal() {
        log.debug("GET /api/games/arsenal");
        JsonNode result = pythonClient.getArsenal();
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/games/arsenal/simulate?qtd=50
     * Simula performance do arsenal nos últimos N concursos.
     */
    @GetMapping("/arsenal/simulate")
    public ResponseEntity<JsonNode> simulateArsenal(@RequestParam(defaultValue = "50") int qtd) {
        log.debug("GET /api/games/arsenal/simulate qtd={}", qtd);
        JsonNode result = pythonClient.simulateArsenal(qtd);
        return ResponseEntity.ok(result);
    }

    /**
     * POST /api/games/ml/predict
     * Previsão de dezenas com Machine Learning.
     */
    @PostMapping("/ml/predict")
    public ResponseEntity<JsonNode> predict(
            @RequestParam(defaultValue = "100") int qtdConcursos,
            @RequestParam(defaultValue = "15") int topN) {
        log.info("POST /api/games/ml/predict qtd={} topN={}", qtdConcursos, topN);
        JsonNode result = pythonClient.predict(qtdConcursos, topN);
        return ResponseEntity.ok(result);
    }

    /**
     * POST /api/games/ml/clusters
     * Clustering de dezenas.
     */
    @PostMapping("/ml/clusters")
    public ResponseEntity<JsonNode> clusters(
            @RequestParam(defaultValue = "100") int qtd,
            @RequestParam(defaultValue = "4") int nClusters) {
        log.info("POST /api/games/ml/clusters qtd={} n={}", qtd, nClusters);
        JsonNode result = pythonClient.getClusters(qtd, nClusters);
        return ResponseEntity.ok(result);
    }
}
