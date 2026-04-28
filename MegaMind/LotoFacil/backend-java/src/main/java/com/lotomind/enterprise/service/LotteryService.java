package com.lotomind.enterprise.service;

import com.lotomind.enterprise.dto.BetRequest;
import com.lotomind.enterprise.entity.Bet;
import com.lotomind.enterprise.entity.User;
import com.lotomind.enterprise.client.PythonAnalysisClient;
import com.lotomind.enterprise.dto.HeatmapResponse;
import com.lotomind.enterprise.exception.ResourceNotFoundException;
import com.lotomind.enterprise.repository.BetRepository;
import com.lotomind.enterprise.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * Serviço de orquestração para operações de loteria.
 * Atua como intermediário entre o controller, o repositório local
 * e o serviço Python de inteligência (via Feign).
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class LotteryService {

    private final BetRepository betRepository;
    private final UserRepository userRepository;
    private final PythonAnalysisClient pythonAnalysisClient;
    private final DrawEventProducer drawEventProducer;

    /**
     * Notifica o sistema sobre um novo sorteio cadastrado.
     * Dispara um evento assíncrono para o motor de inteligência.
     */
    public void notifyNewDraw(int contest) {
        log.info("Manually triggering draw notification for contest #{}", contest);
        drawEventProducer.publishDrawEvent(contest, "CORE_MANAGEMENT_MANUAL");
    }

    /**
     * Busca o mapa de calor de frequências via serviço Python.
     */
    public HeatmapResponse getHeatmap(int lastContests) {
        log.info("Requesting heatmap from Python service for last {} contests", lastContests);
        return pythonAnalysisClient.getHeatmap(lastContests);
    }

    /**
     * Persiste uma nova aposta para o usuário autenticado.
     */
    @Transactional
    public Bet placeBet(Long userId, BetRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));

        Bet bet = Bet.builder()
                .user(user)
                .numbers(request.getNumbers())
                .contest(request.getContest())
                .strategy(request.getStrategy())
                .build();

        Bet saved = betRepository.save(bet);
        log.info("Bet #{} placed by user {} with {} numbers", saved.getId(), userId, request.getNumbers().size());
        return saved;
    }

    /**
     * Lista todas as apostas de um usuário, ordenadas por data.
     */
    @Transactional(readOnly = true)
    public List<Bet> getUserBets(Long userId) {
        return betRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }
}
