from fastapi import FastAPI
from pydantic import BaseModel
from vllm import LLM, SamplingParams
import torch

app = FastAPI()

# Явно указываем устройство CUDA:0 (GPU 1 внутри контейнера)
torch.cuda.set_device(0)

llm = LLM(
    model="Qwen/Qwen2.5-7B-Instruct",
    tensor_parallel_size=1,  # Одна GPU
    gpu_memory_utilization=0.9,
    max_model_len=2048,
    trust_remote_code=True,
    quantization="awq"  # Квантизация для уменьшения памяти
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