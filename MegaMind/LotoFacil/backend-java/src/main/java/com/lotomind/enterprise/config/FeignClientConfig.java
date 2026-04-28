package com.lotomind.enterprise.config;

import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableFeignClients(basePackages = "com.lotomind.enterprise.client")
public class FeignClientConfig {
    // Feign client configuration — additional interceptors / decoders can be added
    // here
}
