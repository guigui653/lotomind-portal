package com.lotterygateway.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;

/**
 * Entidade de concurso de loteria.
 * Suporta tanto Mega-Sena quanto Lotofácil via campo tipoLoteria.
 */
@Entity
@Table(name = "concursos",
       uniqueConstraints = @UniqueConstraint(columnNames = {"numero", "tipo_loteria"}))
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Concurso {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Integer numero;

    @Column(name = "data_sorteio", nullable = false)
    private LocalDate dataSorteio;

    /**
     * Dezenas sorteadas armazenadas como texto CSV.
     * Exemplo Mega-Sena: "05,12,23,34,45,56"
     * Exemplo Lotofácil: "01,02,05,08,10,11,13,14,16,18,19,20,21,24,25"
     */
    @Column(nullable = false, length = 100)
    private String dezenas;

    @Column(name = "tipo_loteria", nullable = false, length = 20)
    @Builder.Default
    private String tipoLoteria = "MEGA_SENA";

    private Integer soma;

    private Integer pares;

    private Integer impares;
}
