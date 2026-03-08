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
async def chat_endpoint(message: ChatMessage, request: Request, background_tasks: BackgroundTasks):
    start_time = time.time()
    
    # A. Recuperar Memória (k=5)
    if message.session_id not in memories:
        memories[message.session_id] = ConversationBufferWindowMemory(k=5, return_messages=True, memory_key="chat_history")
    memory = memories[message.session_id]

    # B. BUSCA SEMÂNTICA (RAG)
    # Busca os 2 trechos mais relevantes no Qdrant
    docs = vector_store.similarity_search(message.text, k=2)
    contexto = "\n".join([d.page_content for d in docs])

    # C. Prompt Estruturado
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"Você é o assistente técnico da Aiwa. Use o contexto abaixo para responder:\n\n{contexto}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])

    # D. Execução
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        openai_api_version=os.getenv("OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0
    )
    
    chain = LLMChain(llm=llm, prompt=prompt, memory=memory)
    ai_response = chain.run(input=message.text)
    
    latency = f"{round(time.time() - start_time, 4)}s"

    # E. Log Assíncrono
    background_tasks.add_task(save_log_to_db, message.session_id, message.text, ai_response, request.client.host, latency)

    return {"answer": ai_response, "session_id": message.session_id}
