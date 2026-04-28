package com.lotofacil.dto;

import java.util.List;

/**
 * Request para backtesting.
 */
public record BacktestRequest(
        List<Integer> jogo,
        int qtdConcursos
) {
    public BacktestRequest {
        if (qtdConcursos <= 0) qtdConcursos = 50;
    }
}
