package com.lotofacil.dto;

import java.util.List;

/**
 * Request para geração de jogos.
 */
public record GameRequest(
        String estrategia,
        int qtdConcursos,
        String melhorJogoNome
) {
    public GameRequest {
        if (estrategia == null || estrategia.isBlank()) estrategia = "equilibrado";
        if (qtdConcursos <= 0) qtdConcursos = 50;
    }
}
