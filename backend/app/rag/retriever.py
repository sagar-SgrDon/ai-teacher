"""
============================================================
STEP 4: RAG Retriever — Knowledge Base se Relevant Info Dhundho
============================================================

🎯 GOAL: User ka question aaye → ChromaDB mein search karo → 
         Top 3 sabse relevant knowledge chunks return karo

📖 EXPLANATION (Hinglish mein):

RAG ka full form hai: Retrieval Augmented Generation
  - Retrieval = Dhundhna (pehle relevant info dhundho)
  - Augmented = Badha hua (us info SE LLM ko smart banao)
  - Generation = Jawab banana (phir LLM jawab de)

Bina RAG ke kya hota:
  User: "Two Sum problem explain karo"
  LLM:  *apni memory se jawab dega* → GALAT ho sakta hai (hallucination)

RAG ke saath:
  User: "Two Sum problem explain karo"
  RAG:  *ChromaDB mein search* → "Two Sum: Use hash map..." milta hai
  LLM:  *RAG ka data + apni memory* → SAHI jawab dega!

Socho aise — agar tumhe exam mein open book milti hai, toh tum
kitaab dekh ke likhte ho (RAG). Bina kitaab ke toh jo yaad hai 
wahi likhoge, jo galat bhi ho sakta hai (hallucination).

FLOW:
  User Question → Embedding mein badlo → ChromaDB search → Top 3 results

🔧 CONCEPTS:
1. Retriever Pattern — search karo, phir result do
2. Semantic Search — meaning ke basis pe dhundho
3. Collection Filtering — English teacher ke liye English data, coding ke liye coding data
============================================================
"""

import chromadb
from sentence_transformers import SentenceTransformer

# Config se settings import karo
# Relative import: "." ka matlab "same package se"
# Matlab: backend/app/config.py se import kar rahe hain
from ..config import CHROMA_DB_PATH, EMBEDDING_MODEL, RAG_TOP_K


class RAGRetriever:
    """
    RAG Retriever class — yeh ChromaDB se relevant documents dhundhta hai.
    
    CLASS kya hai? (Simple explanation)
    ─────────────────────────────────
    Class ek "blueprint" hai. Jaise ek form hota hai —
    form mein likha hai: Naam ___, Age ___, Address ___
    Jab tum form BHARTE ho, toh woh ek "object" ban jaata hai.
    
    Class = Form (template)
    Object = Bhara hua form (actual data ke saath)
    
    Hum class isliye use kar rahe hain kyunki:
    - Model ek baar load karo, baar baar use karo (fast!)
    - ChromaDB connection ek baar banao, baar baar search karo
    
    Agar function hota toh har baar model load hota = SLOW 🐌
    """
    
    def __init__(self):
        """
        __init__ = Constructor = "Object bante hi yeh kaam karo"
        
        Jab bhi koi RAGRetriever() likhega, yeh function chalega
        aur model + ChromaDB connection ready kar dega.
        
        Socho jaise naya phone liya → pehle setup hota hai 
        (SIM daalo, WiFi connect karo) → phir use karo.
        Yeh "setup" wala step hai.
        """
        
        print("🔄 RAG Retriever: Loading embedding model...")
        
        # Embedding model load karo (wahi jo Step 3 mein use kiya tha)
        # self.model = "is object ka apna model"
        # self = "mein khud" (object apne baare mein baat karta hai)
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        
        print("🔄 RAG Retriever: Connecting to ChromaDB...")
        
        # ChromaDB se connect karo
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        print("✅ RAG Retriever ready!")
    
    def search(self, query: str, teacher_type: str = "english", top_k: int = None):
        """
        Main search function — yeh hai RAG ka dil! ❤️
        
        Parameters:
        ──────────
        query       : User ka question (e.g., "How to reverse linked list?")
        teacher_type: "english" ya "coding" — kaunse collection mein search karna hai
        top_k       : Kitne results chahiye (default: config se RAG_TOP_K = 3)
        
        Returns:
        ────────
        List of dicts, har dict mein:
          - "text": document ka content
          - "topic": topic naam  
          - "category": category
          - "distance": kitna close match hai (kam = better)
        
        TYPE HINTS kya hain? (query: str, teacher_type: str)
        ─────────────────────────────────────────────────────
        Yeh Python ko BATATE hain ki kya type ka data aayega.
        str = string (text), int = integer (number)
        Python force nahi karta, but padhne mein easy hota hai.
        Jaise ek signboard — "Yahan se left jao" — follow karna 
        tumhare upar hai, but helpful hai!
        """
        
        if top_k is None:
            top_k = RAG_TOP_K
        
        # ---- Step 1: Sahi collection chuno ----
        # Teacher type ke basis pe collection select karo
        # English teacher → english_knowledge collection
        # Coding tutor → coding_knowledge collection
        collection_name = f"{teacher_type}_knowledge"
        
        try:
            collection = self.client.get_collection(collection_name)
        except Exception as e:
            print(f"❌ Collection '{collection_name}' nahi mili! Error: {e}")
            return []
        
        # ---- Step 2: Query ko embedding mein badlo ----
        # Wahi kaam jo Step 3 mein kiya tha
        # User ka question → 384 numbers ki list
        query_embedding = self.model.encode([query]).tolist()
        
        # ---- Step 3: ChromaDB mein search karo ----
        # query() function sabse "close" documents dhundh ke deta hai
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        
        # ---- Step 4: Results ko clean format mein banao ----
        # ChromaDB nested lists mein data deta hai, hum clean karenge
        search_results = []
        
        if results and results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                result = {
                    "text": results["documents"][0][i],
                    "topic": results["metadatas"][0][i].get("topic", "Unknown"),
                    "category": results["metadatas"][0][i].get("category", "Unknown"),
                    "distance": results["distances"][0][i],
                }
                search_results.append(result)
        
        return search_results
    
    def format_context(self, search_results: list) -> str:
        """
        Search results ko ek sundar text mein badlo — yeh text LLM ko denge.
        
        Kyun? Kyunki LLM ko seedha list of dicts nahi samajh aata.
        Use ek READABLE text chahiye. Jaise:
        
        "Main context:
         1. Topic: Two Sum — Use hash map to find pairs...
         2. Topic: Arrays — Learn about array operations..."
        
        -> str ka matlab: yeh function string return karega
        """
        
        if not search_results:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            # enumerate(list, 1) = list ke saath number bhi do (1 se start)
            part = f"[Source {i}] (Topic: {result['topic']})\n{result['text']}"
            context_parts.append(part)
        
        # "\n\n---\n\n" se alag karo — LLM ko clearly pata chalega
        # ki kahan ek source khatam hua aur doosra shuru hua
        return "\n\n---\n\n".join(context_parts)
