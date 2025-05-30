from fastapi import FastAPI
from pydantic import BaseModel
from vllm import LLM, SamplingParams
import torch

app = FastAPI()

# Явно указываем устройство CUDA:0 (GPU 1 внутри контейнера)
torch.cuda.set_device(1)

llm = LLM(
    model="solidrust/Mistral-7B-Instruct-v0.3-AWQ",
    tensor_parallel_size=1,
    gpu_memory_utilization=0.7,
    quantization="awq",  # AWQ поддерживается этой моделью
    max_model_len=8192, #2048,
    trust_remote_code=True
)

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95

@app.post("/generate")
async def generate_text(request: GenerateRequest):
    sampling_params = SamplingParams(  # Исправлено: правильное присваивание
        temperature=request.temperature,
        top_p=request.top_p,
        max_tokens=request.max_tokens
    )
    outputs = llm.generate([request.prompt], sampling_params)
    return {"text": outputs[0].outputs[0].text.strip()}