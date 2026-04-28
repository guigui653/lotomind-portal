package com.lotomind.enterprise.service;

import com.lotomind.enterprise.dto.LoginRequest;
import com.lotomind.enterprise.dto.LoginResponse;
import com.lotomind.enterprise.entity.User;
import com.lotomind.enterprise.exception.ResourceNotFoundException;
import com.lotomind.enterprise.repository.UserRepository;
import com.lotomind.enterprise.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

/**
 * Serviço de autenticação: login, validação de credenciais e geração de JWT.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    public LoginResponse authenticate(LoginRequest request) {
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new ResourceNotFoundException("Invalid credentials"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new ResourceNotFoundException("Invalid credentials");
        }

        String token = jwtTokenProvider.generateToken(user.getEmail(), user.getRole());
        log.info("User {} authenticated successfully", user.getEmail());

        return LoginResponse.builder()
                .token(token)
                .email(user.getEmail())
                .fullName(user.getFullName())
                .role(user.getRole())
                .build();
    }
}
