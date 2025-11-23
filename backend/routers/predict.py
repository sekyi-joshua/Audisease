from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.prediction_service import predict_audio_bytes

router = APIRouter(tags=["prediction"])


@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    """Upload an audio file and get Parkinson's probability."""
    try:
        audio_bytes = await file.read()
        print("read file. attempting to predict")
        result = predict_audio_bytes(audio_bytes)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
