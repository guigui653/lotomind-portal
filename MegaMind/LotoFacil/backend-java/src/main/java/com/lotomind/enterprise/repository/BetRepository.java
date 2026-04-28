package com.lotomind.enterprise.repository;

import com.lotomind.enterprise.entity.Bet;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface BetRepository extends JpaRepository<Bet, Long> {

    List<Bet> findByUserIdOrderByCreatedAtDesc(Long userId);

    long countByUserId(Long userId);
}
