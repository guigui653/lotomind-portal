package com.lotterygateway.service;

import com.lotterygateway.exception.PythonServiceException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * Serviço de integração com os backends Python (Flask).
 * Usa WebClient (non-blocking) para consumir endpoints do MegaMind e LotoMind.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class PythonIntegrationService {

    private final WebClient webClient;

    @Value("${python.megamind.url}")
    private String megamindUrl;

    @Value("${python.lotomind.url}")
    private String lotomindUrl;

    /**
     * Busca dados gerais do MegaMind (GET /api/dados).
     */
    public Map<String, Object> getMegaMindDados() {
        return callPythonGet(megamindUrl + "/api/dados", "MegaMind");
    }

    /**
     * Valida um jogo no MegaMind (POST /validar).
     */
    public Map<String, Object> validarJogoMega(List<Integer> numeros) {
        return callPythonPost(megamindUrl + "/validar",
                Map.of("numeros", numeros), "MegaMind");
    }

    /**
     * Executa Monte Carlo no MegaMind (POST /monte-carlo).
     */
    public Map<String, Object> monteCarloMega(int quantidade, int topK) {
        return callPythonPost(megamindUrl + "/monte-carlo",
                Map.of("n", quantidade, "top_k", topK), "MegaMind");
    }

    /**
     * Busca dados gerais do LotoMind (GET /api/dados) — se estiver rodando.
     */
    public Map<String, Object> getLotoMindDados() {
        return callPythonGet(lotomindUrl + "/api/dados", "LotoMind");
    }

    // ── Métodos internos ─────────────────────────────────────

    @SuppressWarnings("unchecked")
    private Map<String, Object> callPythonGet(String url, String serviceName) {
        log.debug("GET {} ({})", url, serviceName);

        try {
            return webClient.get()
                    .uri(url)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .timeout(Duration.ofSeconds(30))
                    .block();

        } catch (WebClientRequestException e) {
            log.error("Serviço {} indisponível: {}", serviceName, e.getMessage());
            throw new PythonServiceException(
                    serviceName + " indisponível em " + url, e);

        } catch (WebClientResponseException e) {
            log.error("Serviço {} retornou erro {}: {}",
                    serviceName, e.getStatusCode(), e.getMessage());
            throw new PythonServiceException(
                    serviceName + " retornou erro " + e.getStatusCode(), e);

        } catch (Exception e) {
            log.error("Erro inesperado ao chamar {}: {}", serviceName, e.getMessage(), e);
            throw new PythonServiceException(
                    "Erro ao comunicar com " + serviceName, e);
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> callPythonPost(
            String url, Map<String, Object> body, String serviceName) {
        log.debug("POST {} ({})", url, serviceName);

        try {
            return webClient.post()
                    .uri(url)
                    .header("Content-Type", "application/json")
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .timeout(Duration.ofSeconds(60))  // Monte Carlo pode demorar
                    .block();

        } catch (WebClientRequestException e) {
            log.error("Serviço {} indisponível: {}", serviceName, e.getMessage());
            throw new PythonServiceException(
                    serviceName + " indisponível em " + url, e);

        } catch (WebClientResponseException e) {
            log.error("Serviço {} retornou erro {}: {}",
                    serviceName, e.getStatusCode(), e.getMessage());
            throw new PythonServiceException(
                    serviceName + " retornou erro " + e.getStatusCode(), e);

        } catch (Exception e) {
            log.error("Erro inesperado ao chamar {}: {}", serviceName, e.getMessage(), e);
            throw new PythonServiceException(
                    "Erro ao comunicar com " + serviceName, e);
        }
    }
}
