package com.lotofacil.controller;

import com.lotofacil.dto.AuthResponse;
import com.lotofacil.dto.LoginRequest;
import com.lotofacil.dto.RegisterRequest;
import com.lotofacil.service.AuthService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * Controller de Autenticação — Login e Registro.
 */
@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = { "http://localhost:3000", "http://127.0.0.1:3000" })
public class AuthController {

    private static final Logger log = LoggerFactory.getLogger(AuthController.class);
    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    /**
     * POST /api/auth/login
     * Autentica um usuário e retorna um JWT token.
     */
    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        log.info("Tentativa de login: {}", request.username());
        AuthResponse response = authService.login(request);

        if (response.token() == null) {
            return ResponseEntity.status(401).body(response);
        }

        return ResponseEntity.ok(response);
    }

    /**
     * POST /api/auth/register
     * Registra um novo usuário e retorna um JWT token.
     */
    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@RequestBody RegisterRequest request) {
        log.info("Registro de novo usuário: {}", request.username());
        AuthResponse response = authService.registerUser(request);

        if (response.token() == null) {
            return ResponseEntity.status(409).body(response);
        }

        return ResponseEntity.status(201).body(response);
    }
}
