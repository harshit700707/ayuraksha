import os
from google import genai
from google.genai import types

def analyze_report(image_bytes, language="English"):
    try:
        # --- 100% SAFE API KEY INJECTION ---
        # Ye pehle GEMINI_API_KEY check karega, agar nahi mila toh GOOGLE_API_KEY uthayega
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        
        # Agar dono variables cloud par nahi mile, toh fallback security check (Demo Mode fallback)
        if not api_key:
            return (
                "⚠️ [DEMO FALLBACK MODE: Gemini API Key Not Configured]\n\n"
                "📋 **Complete Blood Count (CBC) & Metabolic Profile Analysis**\n\n"
                "🔍 **Extracted Key Parameters:**\n"
                "- Haemoglobin: 11.2 g/dL (Low | Normal range: 13.5 - 17.5 g/dL)\n"
                "- White Blood Cells (WBC): 12,500 /µL (Elevated | Normal range: 4,000 - 11,000 /µL)\n"
                "- Blood Sugar (Random): 142 mg/dL (Borderline high)\n"
                "- Serum Creatinine: 0.9 mg/dL (Normal | Normal range: 0.6 - 1.2 mg/dL)\n\n"
                "💡 **AI Health Insights & Explanations (Hindi/English mix):**\n"
                "1. **Anaemia Risk (खून की कमी):** Aapka haemoglobin level normal se kam hai. Isse thakan aur kamzori ho sakti hai. Apne aahar mein iron aur Vitamin C rich foods (jaise paalak, anar, nimbu) badhayein.\n"
                "2. **Mild Infection / Inflammation:** WBC count thoda badha hua (12,500) hai. Yeh kisi mild bacterial infection ya internal inflammation ka response ho sakta hai. Agar bukhar ya cold hai, toh physician se consult karein.\n"
                "3. **Sugar Monitoring:** Borderline elevation hai. Fasting sugar check-up recommend kiya jata hai aur junk foods se parhez rakhein.\n\n"
                "👨‍⚕️ **Next Steps (अगला कदम):** Kisi bhi self-medication se bachein. Apne treating physician ko report dikhayein aur unke bataye tests follow karein."
            )
            
        # Ab hum explicitly naye client ko bhej rahe hain bina leak kiye
        client = genai.Client(api_key=api_key) 
        
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg",
        )
        
        prompt = (
            f"You are an advanced AI medical assistant for the AyurRaksha project. "
            f"First, extract all the visible medical text from this report image. "
            f"Then, analyze the data thoroughly and provide clean, patient-friendly insights "
            f"and explanations in {language} language. Keep the formatting structured."
        )
        
        # Free stable tier model
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=[image_part, prompt]
        )
        
        return response.text

    except Exception as e:
        print(f"--- MULTIMODAL API ERROR: {e} ---")
        return f"Analysis Error: {str(e)}"