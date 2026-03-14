"""
============================================================
STEP 1: Test Ollama Connection
============================================================

🎯 GOAL: Verify ki Ollama properly kaam kar raha hai ya nahi

📖 EXPLANATION (Hinglish mein):

Socho Ollama ek "dabba" (box) hai jismein ek chhota sa AI brain 
(phi3:mini) baith ke kaam karta hai. Jab tum Ollama start karte ho, 
yeh apne laptop pe ek "dukaan" khol deta hai address pe:
    http://localhost:11434

"localhost" ka matlab hai → tumhara apna computer
"11434" ka matlab hai → dukaan ka number (port number)

Ab jab hum koi question puchna chahte hain AI se, toh hum ek 
"chitthi" (HTTP request) bhejte hain is dukaan pe. Chitthi mein 
likhte hain:
  - Konsa model use karna hai (phi3:mini)
  - Kya question hai

Phir Ollama jawab wapas bhejta hai.

Yeh script exactly yahi karti hai — ek chhoti si "chitthi" bhejti 
hai Ollama ko, aur check karti hai ki jawab aaya ya nahi.

🔧 CONCEPTS LEARNED:
1. REST API - Ek tarika hai do programs ke beech baat karne ka
2. HTTP POST - Jab hum data BHEJTE hain kisi server ko  
3. JSON - Data ka ek format (jaise dictionary in Python)
4. localhost - Tumhara apna computer as a server

============================================================
"""

import requests  # HTTP requests bhejne ke liye library
import json      # JSON data handle karne ke liye


def test_ollama_connection():
    """
    Step 1: Pehle check karo ki Ollama server chal raha hai ya nahi.
    
    Jaise tum kisi dukaan mein jaane se pehle dekhte ho ki dukaan 
    khuli hai ya nahi — waise hi hum pehle check karte hain ki 
    Ollama ka server "khula" hai ya nahi.
    """
    
    ollama_url = "http://localhost:11434"  # Ollama ka address
    
    print("=" * 50)
    print("🔍 Checking: Kya Ollama server chal raha hai?")
    print("=" * 50)
    
    try:
        # Simple GET request — just "hello, are you there?"
        response = requests.get(ollama_url)
        
        if response.status_code == 200:
            print("✅ Ollama server chal raha hai! (Status: 200 OK)")
            print(f"   Response: {response.text}")
            return True
        else:
            print(f"❌ Ollama response aaya but kuch gadbad hai. Status: {response.status_code}")
            return False
            
    except requests.ConnectionError:
        print("❌ Ollama server nahi chal raha!")
        print("   👉 Fix: Terminal mein 'ollama serve' run karo")
        return False


def test_model_available():
    """
    Step 2: Check karo ki phi3:mini model installed hai ya nahi.
    
    Sochlo Ollama ek library hai, aur models usmein kitaabein hain.
    Hum check kar rahe hain ki "phi3:mini" waali kitaab library 
    mein hai ya nahi.
    """
    
    print("\n" + "=" * 50)
    print("🔍 Checking: Kya phi3:mini model available hai?")
    print("=" * 50)
    
    try:
        # Ollama se poochho — tumhare paas kaunse models hain?
        response = requests.get("http://localhost:11434/api/tags")
        
        if response.status_code == 200:
            data = response.json()  # JSON response ko Python dict mein badlo
            models = data.get("models", [])
            
            print(f"📚 Total models installed: {len(models)}")
            
            for model in models:
                name = model.get("name", "unknown")
                size_bytes = model.get("size", 0)
                size_gb = size_bytes / (1024 ** 3)  # Bytes → GB conversion
                print(f"   📖 {name} (Size: {size_gb:.1f} GB)")
            
            # Check ki phi3:mini hai ya nahi
            model_names = [m.get("name", "") for m in models]
            phi3_found = any("phi3" in name for name in model_names)
            
            if phi3_found:
                print("\n✅ phi3:mini model mil gaya!")
                return True
            else:
                print("\n⚠️ phi3:mini nahi mila. Available models:", model_names)
                print("   👉 Fix: 'ollama pull phi3:mini' run karo")
                return False
        else:
            print(f"❌ Models list nahi mili. Status: {response.status_code}")
            return False
            
    except requests.ConnectionError:
        print("❌ Ollama se baat nahi ho pa rahi!")
        return False


def test_chat_with_model():
    """
    Step 3: Actually ek question poocho phi3:mini se!
    
    Ab tak humne check kiya:
    ✅ Server chal raha hai
    ✅ Model installed hai
    
    Ab asli test — ek question poochte hain!
    
    Hum POST request bhejte hain /api/generate endpoint pe.
    POST ka matlab — hum DATA bhej rahe hain (question).
    GET ka matlab tha — hum sirf DEKH rahe the (no data sent).
    """
    
    print("\n" + "=" * 50)
    print("🤖 Testing: phi3:mini se baat karte hain!")
    print("=" * 50)
    
    # Yeh hai humari "chitthi" (request body)
    payload = {
        "model": "phi3:mini",      # Konsa model use karna hai
        "prompt": "What is Python programming language? Answer in 2 lines only.",
        "stream": False            # Poora jawab ek baar mein do (stream mat karo)
    }
    
    #  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #  "stream: False" ka matlab:
    #  Normally LLM ek-ek word bhejta hai (jaise ChatGPT mein dikhta hai typing effect).
    #  Hum bol rahe hain — nahi bhai, poora jawab ek saath de do.
    #  Beginners ke liye simple hai stream=False se kaam karna.
    
    print(f"\n📤 Question bhej rahe hain: '{payload['prompt']}'")
    print("⏳ Thoda wait karo, model soch raha hai...\n")
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",  # Yeh endpoint hai question poochne ka
            json=payload,                            # JSON format mein data bhejo
            timeout=120                              # 120 seconds tak wait karo max
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", "No response")
            
            # Model ne kitna time liya — yeh bhi interesting info hai
            total_duration = data.get("total_duration", 0)
            duration_seconds = total_duration / 1_000_000_000  # nanoseconds → seconds
            
            print("✅ Model ka jawab aaya!")
            print(f"\n{'─' * 40}")
            print(f"🤖 phi3:mini says:\n{answer}")
            print(f"{'─' * 40}")
            print(f"\n⏱️ Time taken: {duration_seconds:.1f} seconds")
            
            return True
        else:
            print(f"❌ Error! Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.Timeout:
        print("❌ Model ne bahut zyada time le liya (timeout)!")
        print("   Yeh GTX 1650 pe pehli baar thoda slow ho sakta hai.")
        return False
    except requests.ConnectionError:
        print("❌ Ollama se connection nahi ho pa raha!")
        return False


# ============================================================
# MAIN: Sab tests ek saath chalao
# ============================================================

if __name__ == "__main__":
    """
    __name__ == "__main__" ka matlab:
    Yeh code SIRF tab chalega jab tum directly is file ko run karoge.
    Agar koi doosri file ye file import kare, toh yeh nahi chalega.
    
    Socho jaise: "Main apna kaam khud karunga, par agar koi 
    mujhe HELP ke liye bulaye toh yeh kaam nahi karunga"
    """
    
    print("\n🎓 AI TEACHER - Step 1: Ollama Connection Test")
    print("=" * 50)
    
    # Test 1: Server check
    server_ok = test_ollama_connection()
    
    if not server_ok:
        print("\n💡 Pehle Ollama start karo: 'ollama serve'")
        print("   Phir yeh script dobara run karo.")
        exit(1)  # Exit with error code 1
    
    # Test 2: Model check
    model_ok = test_model_available()
    
    if not model_ok:
        print("\n💡 Model install karo: 'ollama pull phi3:mini'")
        exit(1)
    
    # Test 3: Actually baat karo!
    chat_ok = test_chat_with_model()
    
    # Final Report
    print("\n" + "=" * 50)
    print("📊 FINAL REPORT:")
    print("=" * 50)
    print(f"  Server Connection : {'✅ PASS' if server_ok else '❌ FAIL'}")
    print(f"  Model Available   : {'✅ PASS' if model_ok else '❌ FAIL'}")  
    print(f"  Chat Working      : {'✅ PASS' if chat_ok else '❌ FAIL'}")
    
    if server_ok and model_ok and chat_ok:
        print("\n🎉 Sab kuch kaam kar raha hai! Step 1 COMPLETE!")
        print("   Ab hum Step 2 pe ja sakte hain — Knowledge Base banana.")
    else:
        print("\n⚠️ Kuch tests fail hue. Upar ke errors dekho aur fix karo.")
