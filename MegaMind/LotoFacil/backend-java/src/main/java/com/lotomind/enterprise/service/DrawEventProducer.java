package com.lotomind.enterprise.service;

import com.lotomind.enterprise.config.RabbitMQConfig;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class DrawEventProducer {

    private final RabbitTemplate rabbitTemplate;

    public void publishDrawEvent(int contest, String source) {
        log.info("Publishing draw event for contest #{} from source: {}", contest, source);

        Map<String, Object> message = Map.of(
                "contest", contest,
                "timestamp", LocalDateTime.now().toString(),
                "source", source,
                "status", "NEW_DRAW_AVAILABLE");

        rabbitTemplate.convertAndSend(RabbitMQConfig.EXCHANGE, RabbitMQConfig.ROUTING_KEY, message);
    }
}
