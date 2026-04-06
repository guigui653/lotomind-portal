package com.lotterygateway.service;

import com.lotterygateway.dto.LoginRequest;
import com.lotterygateway.dto.LoginResponse;
import com.lotterygateway.dto.RegisterRequest;
import com.lotterygateway.entity.Usuario;
import com.lotterygateway.exception.AuthenticationException;
import com.lotterygateway.repository.UsuarioRepository;
import com.lotterygateway.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

/**
 * Serviço de autenticação: login, registro e geração de JWT.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {

    private final UsuarioRepository usuarioRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    /**
     * Autentica o usuário e retorna um token JWT.
     */
    public LoginResponse authenticate(LoginRequest request) {
        Usuario usuario = usuarioRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new AuthenticationException("Credenciais inválidas"));

        if (!usuario.getActive()) {
            throw new AuthenticationException("Conta desativada");
        }

        if (!passwordEncoder.matches(request.getPassword(), usuario.getPasswordHash())) {
            throw new AuthenticationException("Credenciais inválidas");
        }

        String token = jwtTokenProvider.generateToken(usuario.getEmail(), usuario.getRole());
        log.info("Usuário {} autenticado com sucesso", usuario.getEmail());

        return LoginResponse.builder()
                .token(token)
                .email(usuario.getEmail())
                .fullName(usuario.getFullName())
                .role(usuario.getRole())
                .build();
    }

    /**
     * Registra um novo usuário no sistema.
     */
    public LoginResponse register(RegisterRequest request) {
        if (usuarioRepository.existsByEmail(request.getEmail())) {
            throw new IllegalArgumentException("Email já cadastrado: " + request.getEmail());
        }

        Usuario usuario = Usuario.builder()
                .email(request.getEmail())
                .passwordHash(passwordEncoder.encode(request.getPassword()))
                .fullName(request.getFullName())
                .role("USER")
                .build();

        usuarioRepository.save(usuario);
        log.info("Novo usuário registrado: {}", usuario.getEmail());

        String token = jwtTokenProvider.generateToken(usuario.getEmail(), usuario.getRole());

        return LoginResponse.builder()
                .token(token)
                .email(usuario.getEmail())
                .fullName(usuario.getFullName())
                .role(usuario.getRole())
                .build();
    }
}
