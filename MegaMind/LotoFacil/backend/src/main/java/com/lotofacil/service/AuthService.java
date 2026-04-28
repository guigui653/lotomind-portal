package com.lotofacil.service;

import com.lotofacil.dto.AuthResponse;
import com.lotofacil.dto.LoginRequest;
import com.lotofacil.dto.RegisterRequest;
import com.lotofacil.model.User;
import com.lotofacil.security.JwtTokenProvider;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Serviço de autenticação — In-memory para MVP.
 * Para produção, substitua por UserRepository (JPA + PostgreSQL/MySQL).
 */
@Service
public class AuthService {

    private final JwtTokenProvider tokenProvider;
    private final PasswordEncoder passwordEncoder;

    // In-memory user store (substituir por banco em produção)
    private final Map<String, User> users = new ConcurrentHashMap<>();
    private final AtomicLong idCounter = new AtomicLong(1);

    public AuthService(JwtTokenProvider tokenProvider, PasswordEncoder passwordEncoder) {
        this.tokenProvider = tokenProvider;
        this.passwordEncoder = passwordEncoder;

        // Usuário padrão para testes
        registerUser(new RegisterRequest("admin", "admin123", "admin@lotofacil.com"));
    }

    /**
     * Registra um novo usuário.
     */
    public AuthResponse registerUser(RegisterRequest request) {
        if (users.containsKey(request.username())) {
            return new AuthResponse(null, request.username(), "Usuário já existe");
        }

        String hashedPassword = passwordEncoder.encode(request.password());
        User user = new User(idCounter.getAndIncrement(), request.username(), hashedPassword, request.email());
        users.put(request.username(), user);

        String token = tokenProvider.generateToken(request.username());
        return new AuthResponse(token, request.username(), "Usuário registrado com sucesso");
    }

    /**
     * Autentica um usuário existente.
     */
    public AuthResponse login(LoginRequest request) {
        User user = users.get(request.username());

        if (user == null || !passwordEncoder.matches(request.password(), user.getPassword())) {
            return new AuthResponse(null, request.username(), "Credenciais inválidas");
        }

        String token = tokenProvider.generateToken(request.username());
        return new AuthResponse(token, request.username(), "Login realizado com sucesso");
    }
}
