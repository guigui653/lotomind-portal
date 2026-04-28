package com.lotofacil.dto;

public record AuthResponse(
        String token,
        String username,
        String message
) {}
