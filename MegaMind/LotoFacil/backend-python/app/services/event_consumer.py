import pika
import json
import logging
import asyncio
from app.engine.feature_engineering import FeatureEngineer
from app.engine.ml_engine import XGBMLEngine
from app.engine.monte_carlo import MonteCarloValidator
import os

logger = logging.getLogger(__name__)

class DrawEventConsumer:
    """
    Consumidor assíncrono RabbitMQ para o motor de inteligência Python.
    Escuta notificações de novos sorteios e dispara a pipeline de dados.
    """

    def __init__(self):
        self.host = os.getenv("SPRING_RABBITMQ_HOST", "rabbitmq")
        self.port = int(os.getenv("SPRING_RABBITMQ_PORT", 5672))
        self.user = os.getenv("SPRING_RABBITMQ_USERNAME", "admin")
        self.password = os.getenv("SPRING_RABBITMQ_PASSWORD", "admin_secret")
        
        self.queue = "lotomind.draw.queue"
        self.exchange = "lotomind.draw.exchange"

        # Inicializar Engines
        self.fe = FeatureEngineer()
        self.ml = XGBMLEngine()
        self.mc = MonteCarloValidator()

    def process_message(self, ch, method, properties, body):
        """Callback executado ao receber uma mensagem."""
        try:
            data = json.loads(body)
            contest = data.get("contest")
            logger.info(f"Received draw notification for contest #{contest}")

            # 1. Executar Pipeline de Dados (Simulação do Fluxo)
            self._run_pipeline(contest)

            # Confirmar recebimento
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Successfully processed contest #{contest}")
            
        except Exception as e:
            logger.error(f"Error processing draw message: {e}")
            # Rejeitar e recolocar na fila em caso de erro transiente
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _run_pipeline(self, contest_id: int):
        """Orquestra a pipeline de Inteligência e Precisão."""
        logger.info(f"--- Triggering DS Pipeline for Contest #{contest_id} ---")
        
        # Etapa 1: Feature Engineering (Exemplo conceitual de integração com DB)
        logger.info("Step 1: Running Feature Engineering...")
        # Aqui o Python buscaria os dados do PG e aplicaria a engenharia
        # Para este exemplo modular, focamos na estrutura
        
        # Etapa 2: Inteligência (ML Engine update)
        logger.info("Step 2: Updating XGBoost Model patterns...")
        
        # Etapa 3: Precisão (Monte Carlo Validation para novos palpites)
        logger.info("Step 3: Calculating viability with Monte Carlo...")
        
        logger.info("--- Pipeline Completed Successfully ---")

    def start_consuming(self):
        """Inicia o loop de consumo de mensagens."""
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(self.host, self.port, '/', credentials)
        
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            # Garantir que a fila existe (Idempotência)
            channel.queue_declare(queue=self.queue, durable=True)
            
            # Limitar a 1 mensagem por vez (fair dispatch)
            channel.basic_qos(prefetch_count=1)
            
            channel.basic_consume(queue=self.queue, on_message_callback=self.process_message)

            logger.info(f"Python Consumer started. Listening on {self.queue}...")
            channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError:
            logger.error("Failed to connect to RabbitMQ. Will retry...")
            # Em um sistema real, aqui haveria uma lógica de retry exponencial
