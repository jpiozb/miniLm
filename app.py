from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from typing import Union, List
import uvicorn

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

app = FastAPI()
 
class FeatureExtractionRequest(BaseModel):
    inputs: Union[str, List[str]]
 
@app.post("/")
def feature_extraction(request: FeatureExtractionRequest):
    # 입력받은 텍스트의 임베딩을 생성합니다.
    embeddings = model.encode(request.inputs)
    # 결과를 JSON으로 반환합니다.
    return embeddings.tolist()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
