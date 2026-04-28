package com.lotofacil.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.lotofacil.service.PythonClientService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * Controller de Análise — Proxy para o microsserviço Python.
 * Requer autenticação JWT (configurado no SecurityConfig).
 */
@RestController
@RequestMapping("/api/analysis")
@CrossOrigin(origins = { "http://localhost:3000", "http://127.0.0.1:3000" })
public class AnalysisController {

    private static final Logger log = LoggerFactory.getLogger(AnalysisController.class);
    private final PythonClientService pythonClient;

    public AnalysisController(PythonClientService pythonClient) {
        this.pythonClient = pythonClient;
    }

    /**
     * GET /api/analysis/dashboard?qtd=50
     * Retorna dados completos do dashboard.
     */
    @GetMapping("/dashboard")
    public ResponseEntity<JsonNode> getDashboard(@RequestParam(defaultValue = "50") int qtd) {
        log.debug("GET /api/analysis/dashboard qtd={}", qtd);
        JsonNode data = pythonClient.getDashboard(qtd);
        return ResponseEntity.ok(data);
    }

    /**
     * GET /api/analysis/frequencies?qtd=50
     * Retorna frequências de todas as 25 dezenas.
     */
    @GetMapping("/frequencies")
    public ResponseEntity<JsonNode> getFrequencies(@RequestParam(defaultValue = "50") int qtd) {
        log.debug("GET /api/analysis/frequencies qtd={}", qtd);
        JsonNode data = pythonClient.getFrequencies(qtd);
        return ResponseEntity.ok(data);
    }

    /**
     * GET /api/analysis/heatmap?qtd=50&blocos=5
     * Retorna dados para heatmap de dezenas.
     */
    @GetMapping("/heatmap")
    public ResponseEntity<JsonNode> getHeatmap(
            @RequestParam(defaultValue = "50") int qtd,
            @RequestParam(defaultValue = "5") int blocos) {
        log.debug("GET /api/analysis/heatmap qtd={} blocos={}", qtd, blocos);
        JsonNode data = pythonClient.getHeatmap(qtd, blocos);
        return ResponseEntity.ok(data);
    }
}
