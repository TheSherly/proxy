import httpx
import asyncio
import time
import os  # Importamos o módulo 'os' para acessar as variáveis de ambiente
from fastapi import FastAPI, HTTPException
from asyncio import Queue
import logging

# Configuração básica de logging para vermos o que está acontecendo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configurações da Aplicação ---
# Padrão de Projeto: Proxy - Centralizando o acesso ao recurso externo.
API_BASE_URL = "https://score.hsborges.dev/api"

# *** NOVO: Lendo o Client ID da variável de ambiente ***
# O método os.getenv() busca a variável. Se não encontrar, usa o valor padrão "julio".
CLIENT_ID = os.getenv("PROXY_CLIENT_ID", "Nice")

# --- Cache (Missão 3: Caching) ---
proxy_cache = {}
CACHE_TTL_SECONDS = 300

# --- Componentes do Padrão Producer-Consumer ---

# 1. A Fila Compartilhada (Missão 1: Fila/Buffer)
request_queue: Queue = Queue(maxsize=100)

# 2. O Consumidor (Worker/Scheduler) (Missão 2: Scheduler 1 req/s)
async def request_worker():
    """
    Este é o "Consumidor". Ele processa itens da fila e,
    após sucesso, atualiza o cache.
    """
    logging.info(f"Worker iniciado. Usando CLIENT_ID: '{CLIENT_ID}'")
    while True:
        try:
            cpf, future_result = await request_queue.get()
            logging.info(f"Processando CPF: {cpf} da fila. Itens restantes: {request_queue.qsize()}")

            await asyncio.sleep(1) # CONTROLE DE RATE LIMIT

            async with httpx.AsyncClient() as client:
                try:
                    logging.info(f"Enviando requisição para API externa para o CPF: {cpf}")
                    response = await client.get(
                        f"{API_BASE_URL}/score",
                        params={"cpf": cpf},
                        headers={"accept": "application/json", "client-id": CLIENT_ID}
                    )
                    response.raise_for_status()
                    
                    result_data = response.json()
                    
                    timestamp = time.time()
                    proxy_cache[cpf] = (result_data, timestamp)
                    logging.info(f"Cache atualizado para o CPF: {cpf}")

                    future_result.set_result(result_data)

                except httpx.HTTPStatusError as exc:
                    future_result.set_exception(exc)
                except Exception as e:
                    future_result.set_exception(e)
            
            request_queue.task_done()

        except Exception as e:
            logging.error(f"Erro inesperado no worker: {e}")

# --- Configuração da Aplicação FastAPI ---
app = FastAPI(
    title="Proxy Service com Rate Limiting e Cache",
    description=f"Este proxy está configurado para usar o client-id: '{CLIENT_ID}'"
)

@app.on_event("startup")
async def startup_event():
    """Inicia o worker em background quando a aplicação começa."""
    logging.info("Aplicação iniciada. Criando a task do worker...")
    asyncio.create_task(request_worker())


# 3. O Produtor (Endpoint da API)
@app.get("/proxy/score", tags=["Proxy"])
async def proxy_score_endpoint(cpf: str):
    """
    Este endpoint agora verifica o cache ANTES de enfileirar uma requisição.
    RF1: Expor GET /proxy/score
    """
    if cpf in proxy_cache:
        result_data, timestamp = proxy_cache[cpf]
        age = time.time() - timestamp
        if age < CACHE_TTL_SECONDS:
            logging.info(f"CACHE HIT para o CPF: {cpf}. Retornando dado cacheado.")
            return result_data
        else:
            logging.info(f"CACHE EXPIRED para o CPF: {cpf}. Removendo do cache.")
            del proxy_cache[cpf]
    
    logging.info(f"CACHE MISS para o CPF: {cpf}. Requisição será enfileirada.")
    
    if request_queue.full():
        logging.warning("Fila cheia. Rejeitando a requisição.")
        raise HTTPException(status_code=503, detail="Serviço indisponível, fila de processamento cheia.")

    try:
        future = asyncio.Future()
        await request_queue.put((cpf, future))
        logging.info(f"CPF: {cpf} adicionado à fila. Tamanho atual: {request_queue.qsize()}")
        
        result = await asyncio.wait_for(future, timeout=60.0)
        return result

    except asyncio.TimeoutError:
        logging.error(f"Timeout esperando pelo processamento do CPF: {cpf}")
        raise HTTPException(status_code=504, detail="Tempo de processamento da requisição excedido.")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except Exception as e:
        logging.error(f"Erro ao processar a requisição para CPF {cpf}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

