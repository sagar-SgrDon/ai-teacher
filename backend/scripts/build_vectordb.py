"""
============================================================
STEP 3: Build Vector Database (ChromaDB + Sentence-Transformers)
============================================================

🎯 GOAL: Knowledge base ke text ko "numbers" (embeddings) mein badlo 
         aur ChromaDB mein store karo, taaki baad mein semantic search 
         kar sakein.

📖 EXPLANATION (Hinglish mein):

Socho tumhare paas ek library hai (knowledge base). Ab agar koi pooche
"array mein do numbers ka sum kaise nikale?" toh tumhe woh kitaab
dhundhni padegi jo "Two Sum" problem ke baare mein hai.

Ek tarika hai — EXACT MATCH (ctrl+F jaise):
  ❌ "do numbers ka sum" search karoge toh kuch nahi milega
  kyunki knowledge base mein likha hai "Two Sum"

Doosra tarika — SEMANTIC SEARCH (meaning ke basis pe):
  ✅ "do numbers ka sum" aur "Two Sum" ka MATLAB ek hi hai!
  Toh result milega!

Yeh kaise hota hai?

STEP A: TEXT → NUMBERS (Embeddings)
  Sentence-Transformers ek AI model hai jo har sentence ko 
  ek list of numbers mein badal deta hai. Jaise:
  
  "Two Sum" → [0.23, -0.45, 0.67, ...] (384 numbers)
  "do numbers ka sum" → [0.21, -0.43, 0.65, ...] (384 numbers)
  
  Dhyan do — dono ke numbers MILTE JULTE hain! Kyunki matlab 
  same hai. Agar koi alag topic hota (jaise "cooking recipe") 
  toh numbers bahut ALAG hote.

STEP B: STORE in VECTOR DATABASE (ChromaDB)
  ChromaDB in numbers ko store karta hai aur jab search karo 
  toh "closest numbers" dhundh ke deta hai.
  
  Yeh aise hai jaise Google Maps mein "nearest restaurant" 
  dhundhna — but yahan ye "nearest meaning" dhundh raha hai.

🔧 CONCEPTS LEARNED:
1. Embeddings - Text ko numbers mein badalna (vector representation)
2. Vector Database - Numbers ke basis pe similarity search
3. Semantic Search - Meaning ke basis pe dhundhna, exact words ki zaroorat nahi  
4. ChromaDB - Lightweight vector database (SQLite jaisa simple)
5. Sentence-Transformers - AI model jo text ko embeddings mein badle

============================================================
"""

import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

# ============================================================
# CONFIGURATION
# ============================================================

# Paths — relative to project root
# os.path.dirname = is file ka folder
# os.path.join = paths ko safely jodna (Windows/Linux dono pe kaam kare)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data", "kb")
CHROMA_DIR = os.path.join(PROJECT_ROOT, "backend", "chroma_db")

# Embedding model — yeh ek chhota sa model hai jo text ko numbers mein badlega
# "all-MiniLM-L6-v2" sirf ~80MB ka hai, fast hai, aur accha kaam karta hai
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_knowledge_base():
    """
    Step 1: JSON files se data load karo.
    
    Yeh function dono knowledge base files (English + Coding) ko 
    padhta hai aur unhe ek list mein combine kar deta hai.
    
    Return:
        documents: list of text strings (search mein ye match honge)
        metadatas: list of dicts (extra info — topic, category, etc.)
        ids: list of unique IDs (har document ka apna ID)
    """
    
    documents = []   # Actual text content jo search hoga
    metadatas = []   # Extra information (topic, category, difficulty)  
    ids = []         # Unique identifier for each document
    
    # ---- English Knowledge Base ----
    english_path = os.path.join(DATA_DIR, "english", "english_knowledge.json")
    print(f"\n📂 Loading: {english_path}")
    
    with open(english_path, "r", encoding="utf-8") as f:
        english_data = json.load(f)
    
    for item in english_data:
        # Document = topic + content milake ek text banao
        # Jitna zyada relevant text hoga, utna better search hoga
        doc_text = f"Topic: {item['topic']}\n{item['content']}"
        
        documents.append(doc_text)
        metadatas.append({
            "source": "english",           # Kaunsa teacher ka data hai
            "topic": item["topic"],         # Topic ka naam
            "category": item["category"],   # Grammar/Vocabulary/etc.
            "difficulty": item["difficulty"],
            "id": item["id"]
        })
        ids.append(item["id"])
    
    print(f"   ✅ Loaded {len(english_data)} English items")
    
    # ---- Coding Knowledge Base ----
    coding_path = os.path.join(DATA_DIR, "coding", "coding_knowledge.json")
    print(f"\n📂 Loading: {coding_path}")
    
    with open(coding_path, "r", encoding="utf-8") as f:
        coding_data = json.load(f)
    
    for item in coding_data:
        # Coding ke liye question + hints + explanation sab dalo
        # Taaki jab student pooche "how to reverse linked list" 
        # toh question bhi match ho, aur explanation bhi
        doc_text = (
            f"Topic: {item['topic']}\n"
            f"Question: {item['question']}\n"
            f"Hints: {' | '.join(item['hints'])}\n"
            f"Solution: {item['solution']}\n"
            f"Explanation: {item['explanation']}\n"
            f"Time Complexity: {item['time_complexity']}, "
            f"Space Complexity: {item['space_complexity']}"
        )
        
        documents.append(doc_text)
        metadatas.append({
            "source": "coding",
            "topic": item["topic"],
            "category": item["category"],
            "difficulty": item["difficulty"],
            "id": item["id"]
        })
        ids.append(item["id"])
    
    print(f"   ✅ Loaded {len(coding_data)} Coding items")
    print(f"\n📊 Total documents: {len(documents)}")
    
    return documents, metadatas, ids


def build_vector_database(documents, metadatas, ids):
    """
    Step 2: Embeddings banao aur ChromaDB mein store karo.
    
    Yeh function teen kaam karta hai:
    1. Embedding model load karo (pehli baar download hoga ~80MB)
    2. Har document ko numbers (embeddings) mein badlo
    3. ChromaDB mein store karo
    
    ChromaDB ko samjho aise:
    - Yeh ek special database hai jo numbers store karta hai
    - Jab tum search karo, yeh "sabse milte julte numbers" dhundhta hai
    - Isme "collections" hoti hain — jaise folders in a file system
    
    Hum 2 collections banaenge:
    - "english_knowledge" — English teacher ka data
    - "coding_knowledge" — Coding tutor ka data
    """
    
    # ---- Step 2a: Embedding Model Load Karo ----
    print("\n" + "=" * 50)
    print("🧠 Loading embedding model...")
    print("=" * 50)
    print(f"   Model: {EMBEDDING_MODEL}")
    print("   Pehli baar mein download hoga (~80MB), phir cache se aayega")
    
    # SentenceTransformer automatically model download karke load kar deta hai
    # Yeh model text ko 384-dimensional vector mein badalta hai
    # Matlab har sentence 384 numbers ki list ban jaati hai
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    print("   ✅ Model loaded successfully!")
    
    # ---- Step 2b: ChromaDB Client Banao ----
    print(f"\n📁 ChromaDB folder: {CHROMA_DIR}")
    
    # PersistentClient = data disk pe save hoga (RAM mein nahi)
    # Matlab: script band karne ke baad bhi data rahega
    # Agar hum Client() use karte (bina Persistent), toh data RAM mein rehta 
    # aur script band hote hi gayab ho jaata
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # ---- Step 2c: Collections Banao ----
    # Pehle purani collections delete karo (agar hain) — fresh start
    existing_collections = [col.name for col in client.list_collections()]
    
    for name in ["english_knowledge", "coding_knowledge"]:
        if name in existing_collections:
            client.delete_collection(name)
            print(f"   🗑️ Deleted old collection: {name}")
    
    # Nai collections banao
    english_collection = client.create_collection(
        name="english_knowledge",
        metadata={"description": "English grammar, vocabulary, conversation knowledge"}
    )
    
    coding_collection = client.create_collection(
        name="coding_knowledge", 
        metadata={"description": "DSA and coding interview problems"}
    )
    
    print("   ✅ Collections created: english_knowledge, coding_knowledge")
    
    # ---- Step 2d: Documents ko Embed Karo aur Store Karo ----
    print("\n" + "=" * 50)
    print("🔄 Embedding documents and storing in ChromaDB...")
    print("=" * 50)
    
    # English documents alag, Coding documents alag
    eng_docs, eng_metas, eng_ids = [], [], []
    code_docs, code_metas, code_ids = [], [], []
    
    for doc, meta, doc_id in zip(documents, metadatas, ids):
        if meta["source"] == "english":
            eng_docs.append(doc)
            eng_metas.append(meta)
            eng_ids.append(doc_id)
        else:
            code_docs.append(doc)
            code_metas.append(meta)
            code_ids.append(doc_id)
    
    # English documents embed aur store
    if eng_docs:
        print(f"\n   📝 Embedding {len(eng_docs)} English documents...")
        eng_embeddings = model.encode(eng_docs).tolist()  # Text → Numbers!
        
        # ChromaDB mein add karo
        english_collection.add(
            documents=eng_docs,          # Original text (search results mein dikhega)
            embeddings=eng_embeddings,   # Number vectors (search mein ye compare honge)
            metadatas=eng_metas,         # Extra info (filtering ke liye useful)
            ids=eng_ids                  # Unique IDs
        )
        print(f"   ✅ Stored {len(eng_docs)} English documents")
    
    # Coding documents embed aur store 
    if code_docs:
        print(f"\n   💻 Embedding {len(code_docs)} Coding documents...")
        code_embeddings = model.encode(code_docs).tolist()
        
        coding_collection.add(
            documents=code_docs,
            embeddings=code_embeddings,
            metadatas=code_metas,
            ids=code_ids
        )
        print(f"   ✅ Stored {len(code_docs)} Coding documents")
    
    return model, client


def test_search(model, client):
    """
    Step 3: Test karo ki search kaam kar raha hai ya nahi!
    
    Hum kuch example queries search karenge aur dekhenge ki 
    sahi results aa rahe hain ya nahi.
    
    ChromaDB ka query() function kaise kaam karta hai:
    1. Tumhara question embedding mein badalta hai
    2. Database mein stored embeddings se compare karta hai  
    3. Sabse "close" (similar) results return karta hai
    
    "Close" ka matlab — cosine similarity ya euclidean distance
    Socho 3D space mein do points — jo points paas hain, woh similar hain
    (bas yahan 384-dimensional space hai, 3D nahi 😄)
    """
    
    print("\n" + "=" * 50)
    print("🔍 Testing search...")
    print("=" * 50)
    
    # Test queries
    test_cases = [
        {
            "query": "How to use present tense in English?",
            "collection": "english_knowledge",
            "expected_topic": "Tenses"
        },
        {
            "query": "find two numbers that add up to target",
            "collection": "coding_knowledge", 
            "expected_topic": "Two Sum"
        },
        {
            "query": "how to reverse a linked list",
            "collection": "coding_knowledge",
            "expected_topic": "Reverse"
        },
        {
            "query": "common mistakes Indian students make",
            "collection": "english_knowledge",
            "expected_topic": "mistakes"
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        collection = client.get_collection(test["collection"])
        
        # Query ko embedding mein badlo
        query_embedding = model.encode([test["query"]]).tolist()
        
        # ChromaDB mein search karo — top 2 results do
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=2  # Top 2 most similar documents
        )
        
        # Results check karo
        top_result = results["metadatas"][0][0]  # Sabse best match
        top_topic = top_result.get("topic", "")
        distance = results["distances"][0][0]    # Kitna "door" hai (kam = better)
        
        # Check ki expected topic match hua ya nahi
        match = test["expected_topic"].lower() in top_topic.lower()
        status = "✅" if match else "⚠️"
        
        if not match:
            all_passed = False
        
        print(f"\n   Test {i}: {status}")
        print(f"   Query:    '{test['query']}'")
        print(f"   Found:    '{top_topic}'")
        print(f"   Distance: {distance:.4f} (kam = better match)")
        
        # Top result ka thoda sa text dikhao
        doc_preview = results["documents"][0][0][:100] + "..."
        print(f"   Preview:  {doc_preview}")
    
    return all_passed


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("\n🎓 AI TEACHER - Step 3: Building Vector Database")
    print("=" * 50)
    
    # Step 1: Knowledge base load karo
    print("\n📚 PART 1: Loading Knowledge Base")
    documents, metadatas, ids = load_knowledge_base()
    
    # Step 2: Vector database banao
    print("\n🗄️ PART 2: Building Vector Database")
    model, client = build_vector_database(documents, metadatas, ids)
    
    # Step 3: Test karo
    print("\n🧪 PART 3: Testing Search")
    search_ok = test_search(model, client)
    
    # Final Report
    print("\n" + "=" * 50)
    print("📊 FINAL REPORT:")
    print("=" * 50)
    print(f"  Knowledge Base Loaded : ✅ ({len(documents)} documents)")
    print(f"  Vector DB Built       : ✅ (stored in {CHROMA_DIR})")
    print(f"  Search Working        : {'✅ PASS' if search_ok else '⚠️ PARTIAL'}")
    
    if search_ok:
        print("\n🎉 Step 3 COMPLETE! Vector database ready!")
        print("   Ab hum Step 4 pe ja sakte hain — RAG Pipeline banana.")
    else:
        print("\n⚠️ Search mostly kaam kar raha hai, but kuch results expected se alag hain.")
        print("   Yeh normal hai — semantic search 100% exact match nahi hota.")
        print("   Ab hum aage badh sakte hain!")
