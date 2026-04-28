from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text
from app.core.database import async_session
from app.services.prediction_generator import PredictionGenerator

router = APIRouter()
generator = PredictionGenerator()

class PredictionCreate(BaseModel):
    numbers: List[int]
    concurso_alvo: Optional[int] = None
    strategy_name: Optional[str] = "balanced"

class PredictionResponse(BaseModel):
    id: int
    numbers: List[int]
    created_at: datetime
    concurso_alvo: Optional[int]

@router.get("/generate-prediction")
async def generate_prediction(strategy: str = "balanced"):
    """Gera um palpite inteligente."""
    return await generator.generate_prediction(strategy)

@router.post("/predictions", status_code=201)
async def save_prediction(prediction: PredictionCreate):
    """Salva um palpite no histórico."""
    async with async_session() as session:
        try:
            await session.execute(
                text("INSERT INTO lotomind.predictions (numbers, concurso_alvo, strategy_name) VALUES (:numbers, :concurso_alvo, :strategy_name)"),
                {"numbers": prediction.numbers, "concurso_alvo": prediction.concurso_alvo, "strategy_name": prediction.strategy_name}
            )
            await session.commit()
            return {"message": "Palpite salvo com sucesso!"}
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions")
async def list_predictions():
    """Lista os últimos 50 palpites salvos."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id, numbers, concurso_alvo, created_at FROM lotomind.predictions ORDER BY created_at DESC LIMIT 50")
        )
        rows = result.fetchall()
        
        return [
            {
                "id": row.id,
                "numbers": row.numbers,
                "concurso_alvo": row.concurso_alvo,
                "created_at": row.created_at.isoformat()
            }
            for row in rows
        ]
