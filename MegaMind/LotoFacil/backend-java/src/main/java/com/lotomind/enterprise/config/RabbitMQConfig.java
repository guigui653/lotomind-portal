package com.lotomind.enterprise.config;

import org.springframework.amqp.core.*;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

    public static final String EXCHANGE = "lotomind.draw.exchange";
    public static final String QUEUE = "lotomind.draw.queue";
    public static final String ROUTING_KEY = "lotomind.draw.new";

    @Bean
    public TopicExchange drawExchange() {
        return new TopicExchange(EXCHANGE);
    }

    @Bean
    public Queue drawQueue() {
        return QueueBuilder.durable(QUEUE).build();
    }

    @Bean
    public Binding drawBinding(Queue drawQueue, TopicExchange drawExchange) {
        return BindingBuilder.bind(drawQueue).to(drawExchange).with(ROUTING_KEY);
    }

    @Bean
    public MessageConverter jsonMessageConverter() {
        return new Jackson2JsonMessageConverter();
    }
}
