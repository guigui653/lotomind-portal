package com.lotterygateway.dto;

import lombok.*;
import java.util.Map;

/**
 * DTO que encapsula a resposta de estatísticas vindas do serviço Python.
 * Como o JSON do Python é dinâmico, usa-se Map para flexibilidade.
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class EstatisticaResponse {

    private ConcursoDTO concurso;
    private Map<String, Object> estatisticas;
    private String fonte;     // "megamind" ou "lotomind"
    private String status;
}
