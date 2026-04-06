package com.lotterygateway.exception;

/**
 * Exceção para quando o serviço Python (Flask) está indisponível
 * ou retorna erro. Mapeada para HTTP 502 Bad Gateway.
 */
public class PythonServiceException extends RuntimeException {
    public PythonServiceException(String message) {
        super(message);
    }

    public PythonServiceException(String message, Throwable cause) {
        super(message, cause);
    }
}
