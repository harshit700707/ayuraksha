import os
from google import genai
from google.genai import types

def analyze_report(image_bytes, language="English"):
    """
    Direct image bytes ko Gemini ko bhej kar OCR + Analysis dono ek saath karwane ke liye.
    """
    try:
        # Naya Client initialize karo (Ye Render ke Environment Variables se GEMINI_API_KEY utha lega)
        client = genai.Client(api_key='AIzaSyDizLZhSnWQcdQkelcqn5btpP_aTBj6XkY')
        
        # Image bytes ko Gemini ke samajhne layak format mein convert karo
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg", # Agar png ho toh image/png bhi chalega, standard image/jpeg sahi kaam karta hai
        )
        
        # Ek strong medical prompt jo OCR + Analysis dono karega
        prompt = (
            f"You are an advanced AI medical assistant for the AyurRaksha project. "
            f"First, extract all the visible medical text from this report image. "
            f"Then, analyze the data thoroughly and provide clean, patient-friendly insights "
            f"and explanations in {language} language. Keep the formatting structured."
        )
        
        # Direct image aur prompt dono bhej do
        response = client.models.generate_content(
            model='gemini-2.0-flash', # Flash multimodal hai aur bohot tez hai
            contents=[image_part, prompt]
        )
        
        return response.text

    except Exception as e:
        print(f"--- MULTIMODAL API ERROR: {e} ---")
        return f"Analysis Error: {str(e)}"