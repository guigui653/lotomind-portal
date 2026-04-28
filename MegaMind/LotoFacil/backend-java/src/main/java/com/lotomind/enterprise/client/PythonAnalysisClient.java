package com.lotomind.enterprise.client;

import com.lotomind.enterprise.dto.HeatmapResponse;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * Feign Client para comunicação com o serviço Python de Inteligência.
 * <p>
 * Este client atua como proxy reverso tipado, permitindo que o backend Java
 * consuma os endpoints analíticos do FastAPI de forma declarativa.
 */
@FeignClient(name = "python-analysis", url = "${python.service.url}")
public interface PythonAnalysisClient {

    @GetMapping("/api/v1/analysis/heatmap")
    HeatmapResponse getHeatmap(@RequestParam(defaultValue = "50") int lastContests);

    @GetMapping("/api/v1/analysis/predictions")
    Object getPredictions(@RequestParam(defaultValue = "10") int topN);
}
