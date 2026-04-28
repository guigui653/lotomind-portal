package com.lotomind.enterprise.controller;

import com.lotomind.enterprise.dto.BetRequest;
import com.lotomind.enterprise.dto.HeatmapResponse;
import com.lotomind.enterprise.entity.Bet;
import com.lotomind.enterprise.service.LotteryService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Controller principal de loteria.
 * <p>
 * Expõe endpoints para:
 * - Consultar o mapa de calor (proxy para o serviço Python via Feign)
 * - Registrar e listar apostas do usuário
 * <p>
 * Todos os endpoints estão sob {@code /api/v1/lottery} (context-path +
 * mapping).
 */
@RestController
@RequestMapping("/lottery")
@RequiredArgsConstructor
@Slf4j
public class LotteryController {

    private final LotteryService lotteryService;

    // ═══════════════════════════════════════════════════════════
    // ANÁLISE (Python Intelligence Proxy)
    // ═══════════════════════════════════════════════════════════

    /**
     * GET /api/v1/lottery/heatmap
     * <p>
     * Retorna o mapa de calor de frequência dos números da Lotofácil.
     * Os dados são calculados pelo serviço Python e cacheados via Redis.
     *
     * @param lastContests número de concursos a considerar (default 50)
     * @return frequência de cada número (1-25)
     */
    @GetMapping("/heatmap")
    public ResponseEntity<HeatmapResponse> getHeatmap(
            @RequestParam(defaultValue = "50") int lastContests) {

        log.info("GET /lottery/heatmap — lastContests={}", lastContests);
        HeatmapResponse heatmap = lotteryService.getHeatmap(lastContests);
        return ResponseEntity.ok(heatmap);
    }

    // ═══════════════════════════════════════════════════════════
    // APOSTAS (Persistência Local)
    // ═══════════════════════════════════════════════════════════

    /**
     * POST /api/v1/lottery/bets
     * <p>
     * Registra uma nova aposta para o usuário autenticado.
     * Valida que o array contém entre 15 e 20 números.
     */
    @PostMapping("/bets")
    public ResponseEntity<Bet> placeBet(@Valid @RequestBody BetRequest request) {
        // TODO: Extrair userId do SecurityContext (JWT) após implementação completa
        Long userId = 1L;
        Bet bet = lotteryService.placeBet(userId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(bet);
    }

    /**
     * GET /api/v1/lottery/bets
     * <p>
     * Lista todas as apostas do usuário autenticado.
     */
    @GetMapping("/bets")
    public ResponseEntity<List<Bet>> getUserBets() {
        // TODO: Extrair userId do SecurityContext (JWT) após implementação completa
        Long userId = 1L;
        List<Bet> bets = lotteryService.getUserBets(userId);
        return ResponseEntity.ok(bets);
    }
}
