package com.lotomind.enterprise.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class HeatmapResponse {

    private List<Integer> numbers;
    private List<Integer> frequencies;
    private Map<String, Object> metadata;
}
