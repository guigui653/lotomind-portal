package com.lotterygateway.controller;

import com.lotterygateway.dto.ConcursoDTO;
import com.lotterygateway.dto.EstatisticaResponse;
import com.lotterygateway.service.ConcursoService;
import com.lotterygateway.service.PythonIntegrationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * Controller de estatísticas e concursos.
 * Todas as rotas requerem autenticação JWT (configurado no SecurityConfig).
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Slf4j
public class EstatisticaController {

    private final ConcursoService concursoService;
    private final PythonIntegrationService pythonService;

    // ═══════════════════════════════════════════════════════════
    //  ESTATÍSTICAS MEGA-SENA (Proxy para MegaMind Flask)
    // ═══════════════════════════════════════════════════════════

    /**
     * GET /api/estatisticas/mega/{concurso}
     *
     * Fluxo:
     * 1. Valida o token JWT (feito pelo filtro de segurança)
     * 2. Verifica se o concurso existe no banco SQL
     * 3. Chama o MegaMind (Python) para calcular estatísticas
     * 4. Retorna JSON combinando dados do SQL + Python
     */
    @GetMapping("/estatisticas/mega/{concurso}")
    public ResponseEntity<EstatisticaResponse> getEstatisticasMega(
            @PathVariable Integer concurso) {

        log.info("GET /api/estatisticas/mega/{}", concurso);

        // 1) Busca concurso no SQL
        ConcursoDTO concursoDTO = concursoService.buscarConcurso(concurso, "MEGA_SENA");

        // 2) Chama serviço Python para estatísticas
        Map<String, Object> estatisticasPython = pythonService.getMegaMindDados();

        // 3) Combina e retorna
        EstatisticaResponse response = EstatisticaResponse.builder()
                .concurso(concursoDTO)
                .estatisticas(estatisticasPython)
                .fonte("megamind")
                .status("ok")
                .build();

        return ResponseEntity.ok(response);
    }

    /**
     * GET /api/estatisticas/mega/dados
     * Proxy direto para o endpoint /api/dados do MegaMind.
     */
    @GetMapping("/estatisticas/mega/dados")
    public ResponseEntity<Map<String, Object>> getDadosMega() {
        log.info("GET /api/estatisticas/mega/dados — proxy para MegaMind");
        Map<String, Object> dados = pythonService.getMegaMindDados();
        return ResponseEntity.ok(dados);
    }

    /**
     * POST /api/estatisticas/mega/validar
     * Proxy para validação de jogo no MegaMind.
     */
    @PostMapping("/estatisticas/mega/validar")
    public ResponseEntity<Map<String, Object>> validarJogoMega(
            @RequestBody Map<String, List<Integer>> body) {

        List<Integer> numeros = body.get("numeros");
        if (numeros == null || numeros.isEmpty()) {
            throw new IllegalArgumentException("Campo 'numeros' é obrigatório");
        }

        log.info("POST /api/estatisticas/mega/validar — {} números", numeros.size());
        Map<String, Object> resultado = pythonService.validarJogoMega(numeros);
        return ResponseEntity.ok(resultado);
    }

    /**
     * POST /api/estatisticas/mega/monte-carlo
     * Proxy para simulação Monte Carlo no MegaMind.
     */
    @PostMapping("/estatisticas/mega/monte-carlo")
    public ResponseEntity<Map<String, Object>> monteCarloMega(
            @RequestBody Map<String, Integer> body) {

        int n = body.getOrDefault("n", 100000);
        int topK = body.getOrDefault("top_k", 10);

        log.info("POST /api/estatisticas/mega/monte-carlo — n={}, topK={}", n, topK);
        Map<String, Object> resultado = pythonService.monteCarloMega(n, topK);
        return ResponseEntity.ok(resultado);
    }

    // ═══════════════════════════════════════════════════════════
    //  CONCURSOS (CRUD — SQL)
    // ═══════════════════════════════════════════════════════════

    /**
     * GET /api/concursos?tipo=MEGA_SENA
     * Lista concursos cadastrados no banco.
     */
    @GetMapping("/concursos")
    public ResponseEntity<List<ConcursoDTO>> listarConcursos(
            @RequestParam(defaultValue = "MEGA_SENA") String tipo) {

        List<ConcursoDTO> concursos = concursoService.listarConcursos(tipo);
        return ResponseEntity.ok(concursos);
    }

    /**
     * POST /api/concursos
     * Cadastra um novo concurso (somente ADMIN).
     */
    @PostMapping("/concursos")
    public ResponseEntity<ConcursoDTO> cadastrarConcurso(
            @RequestBody ConcursoDTO dto) {

        ConcursoDTO saved = concursoService.cadastrarConcurso(dto);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }
}
