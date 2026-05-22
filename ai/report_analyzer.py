import os
from google import genai
from google.genai import types

def analyze_report(image_bytes, language="English"):
    try:
        # --- 100% SAFE API KEY INJECTION ---
        # Ye pehle GEMINI_API_KEY check karega, agar nahi mila toh GOOGLE_API_KEY uthayega
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        
        # Agar dono variables cloud par nahi mile, toh fallback security check
        if not api_key:
            return "Analysis Error: Cloud environment mein API Key nahi mili. Render Environment settings check karein."
            
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