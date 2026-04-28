package com.lotomind.enterprise.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BetRequest {

    @NotEmpty(message = "Numbers are required")
    @Size(min = 15, max = 20, message = "Lotofácil bets must contain 15 to 20 numbers")
    private List<Integer> numbers;

    private Integer contest;

    private String strategy;
}
