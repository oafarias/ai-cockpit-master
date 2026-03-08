import os
from langchain_openai import AzureOpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configurações da Azure (mesmas do seu main.py)
embeddings = AzureOpenAIEmbeddings(
    azure_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
    openai_api_version=os.getenv("AZURE_EMBEDDING_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

client = QdrantClient(host=os.getenv("QDRANT_HOST"), port=6333)
collection_name = "aiwa_knowledge"

# Exemplo de conhecimento técnico da Aiwa
conhecimento_aiwa = [
    "A Smart TV Aiwa 55 polegadas possui tecnologia Android TV e comando de voz no controle remoto.",
    "O suporte técnico da Aiwa atende pelo telefone 0800-555-0000 de segunda a sexta.",
    "Para resetar a caixa de som Aiwa Boombox, segure os botões Bluetooth e Volume+ por 10 segundos.",
    "A garantia dos produtos Mondial e Aiwa é de 1 ano para defeitos de fabricação."
]

def ingest():
    # Cria a coleção se não existir
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name="aiwa_knowledge",
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
        )
    
    # Sobe os textos para o Qdrant
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    vector_store.add_texts(conhecimento_aiwa)
    print("🚀 Conhecimento injetado com sucesso no Qdrant!")

if __name__ == "__main__":
    ingest()
