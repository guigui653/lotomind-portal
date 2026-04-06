package com.lotterygateway.dto;

import lombok.*;
import java.time.LocalDate;
import java.util.List;

/**
 * DTO de Concurso — expõe dados para o frontend sem informações internas.
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ConcursoDTO {

    private Integer numero;
    private LocalDate dataSorteio;
    private List<Integer> dezenas;
    private String tipoLoteria;
    private Integer soma;
    private Integer pares;
    private Integer impares;
}
