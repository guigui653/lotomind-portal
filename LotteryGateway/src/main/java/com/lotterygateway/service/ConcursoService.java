package com.lotterygateway.service;

import com.lotterygateway.dto.ConcursoDTO;
import com.lotterygateway.entity.Concurso;
import com.lotterygateway.exception.ResourceNotFoundException;
import com.lotterygateway.repository.ConcursoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Serviço de gerenciamento de concursos.
 * Faz CRUD no SQL e converte entre Entity ↔ DTO.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ConcursoService {

    private final ConcursoRepository concursoRepository;

    /**
     * Busca um concurso por número e tipo de loteria.
     */
    @Transactional(readOnly = true)
    public ConcursoDTO buscarConcurso(Integer numero, String tipoLoteria) {
        Concurso concurso = concursoRepository
                .findByNumeroAndTipoLoteria(numero, tipoLoteria)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Concurso " + numero + " (" + tipoLoteria + ") não encontrado"));
        return toDTO(concurso);
    }

    /**
     * Lista todos os concursos de um tipo de loteria.
     */
    @Transactional(readOnly = true)
    public List<ConcursoDTO> listarConcursos(String tipoLoteria) {
        return concursoRepository.findByTipoLoteriaOrderByNumeroDesc(tipoLoteria)
                .stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    /**
     * Cadastra um novo concurso.
     */
    @Transactional
    public ConcursoDTO cadastrarConcurso(ConcursoDTO dto) {
        if (concursoRepository.existsByNumeroAndTipoLoteria(dto.getNumero(), dto.getTipoLoteria())) {
            throw new IllegalArgumentException(
                    "Concurso " + dto.getNumero() + " já existe para " + dto.getTipoLoteria());
        }

        String dezenasStr = dto.getDezenas().stream()
                .map(d -> String.format("%02d", d))
                .collect(Collectors.joining(","));

        Concurso concurso = Concurso.builder()
                .numero(dto.getNumero())
                .dataSorteio(dto.getDataSorteio() != null ? dto.getDataSorteio() : LocalDate.now())
                .dezenas(dezenasStr)
                .tipoLoteria(dto.getTipoLoteria() != null ? dto.getTipoLoteria() : "MEGA_SENA")
                .soma(dto.getSoma() != null ? dto.getSoma() : dto.getDezenas().stream().mapToInt(Integer::intValue).sum())
                .pares(dto.getPares() != null ? dto.getPares() : (int) dto.getDezenas().stream().filter(d -> d % 2 == 0).count())
                .impares(dto.getImpares() != null ? dto.getImpares() : (int) dto.getDezenas().stream().filter(d -> d % 2 != 0).count())
                .build();

        Concurso saved = concursoRepository.save(concurso);
        log.info("Concurso #{} ({}) cadastrado", saved.getNumero(), saved.getTipoLoteria());
        return toDTO(saved);
    }

    // ── Conversão Entity → DTO ─────────────────────────────

    private ConcursoDTO toDTO(Concurso c) {
        List<Integer> dezenas = Arrays.stream(c.getDezenas().split(","))
                .map(String::trim)
                .map(Integer::parseInt)
                .collect(Collectors.toList());

        return ConcursoDTO.builder()
                .numero(c.getNumero())
                .dataSorteio(c.getDataSorteio())
                .dezenas(dezenas)
                .tipoLoteria(c.getTipoLoteria())
                .soma(c.getSoma())
                .pares(c.getPares())
                .impares(c.getImpares())
                .build();
    }
}
