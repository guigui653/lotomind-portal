package com.lotofacil.dto;

public record RegisterRequest(
        String username,
        String password,
        String email
) {}
