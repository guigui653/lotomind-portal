package com.lotterygateway.repository;

import com.lotterygateway.entity.Concurso;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface ConcursoRepository extends JpaRepository<Concurso, Long> {

    Optional<Concurso> findByNumeroAndTipoLoteria(Integer numero, String tipoLoteria);

    List<Concurso> findByTipoLoteriaOrderByNumeroDesc(String tipoLoteria);

    boolean existsByNumeroAndTipoLoteria(Integer numero, String tipoLoteria);
}
