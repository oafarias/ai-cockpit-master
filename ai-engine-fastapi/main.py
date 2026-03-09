from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware  # <-- Importação nova
from pydantic import BaseModel
import os, time, psycopg2
from qdrant_client import QdrantClient
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
import httpx

app = FastAPI(title="AI Engine - Cockpit")

# --- CONFIGURAÇÃO DE CORS (O Passaporte do Frontend) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção real, você colocaria ["https://chat.aaleff.me"]
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, etc.
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

# ... Resto do seu código (ChatMessage, memories, embeddings, etc.)
class ChatMessage(BaseModel):
    text: str
    session_id: str

memories = {}

# 1. Configuração de Embeddings (Singular para bater com o ingest)
embeddings = AzureOpenAIEmbeddings(
    azure_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
    openai_api_version=os.getenv("AZURE_EMBEDDING_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

# 2. Configuração do Vector Store
vector_store = QdrantVectorStore(
    client=QdrantClient(host=os.getenv("QDRANT_HOST"), port=6333),
    collection_name="aiwa_knowledge",
    embedding=embeddings,
)

# --- FUNÇÃO DE LOG ---
def save_log_to_db(session_id, message, response, ip, latency):
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"), host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        cur.execute("INSERT INTO logs_interacao (session_id, message_text, ai_response, client_ip, latency) VALUES (%s, %s, %s, %s, %s)",
                    (session_id, message, response, ip, latency))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e: print(f"Erro log: {e}")

@app.post("/v1/chat")
async def chat_endpoint(message: ChatMessage):
    n8n_url = "http://n8n-automation:5678/webhook/chat-aiwa" # Use o nome do serviço no Docker
    
    async with httpx.AsyncClient() as client:
        response = await client.post(n8n_url, json={
            "text": message.text,
            "session_id": message.session_id
        }, timeout=60.0) # Aumente o timeout porque IA demora
        
    return response.json()