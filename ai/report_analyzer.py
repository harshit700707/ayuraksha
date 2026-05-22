import os
import pytesseract
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

# Windows local testing ke liye path (agar zaroorat ho toh uncomment kar lena)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Cloud/Render Docker ke liye exact path definition
if os.name != 'nt':  # Agar Windows nahi hai (LInux/Render hai)
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

load_dotenv()

# OpenRouter Client Initialization
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def analyze_report(image_path, language):
    try:
        # --- 1. MEMORY OPTIMIZATION (Prevent SIGKILL/Out of Memory) ---
        image = Image.open(image_path)
        
        # Image ka size chota karo taaki Render ki RAM crash na ho
        image.thumbnail((1200, 1200))
        
        # Black & White (Grayscale) convert karo taaki OCR fast chale aur memory bache
        image = image.convert('L')

        # --- 2. OCR TEXT EXTRACTION ---
        extracted_text = pytesseract.image_to_string(image)

        if not extracted_text.strip():
            return "Error: Image se koi text nahi extracted ho saka. Kripya saaf photo upload karein."

        # --- 3. PROMPT CREATION ---
        prompt = f"""
        Analyze this medical report text carefully.
        
        Language of Response: {language}
        
        Report Text:
        {extracted_text}
        
        Provide the explanation strictly in the following structured format:
        1. Abnormal values
        2. Possible diseases
        3. Suggestions
        4. Simple summary
        """

        # --- 4. OPENROUTER API CALL (Optimized Model) ---
        # Note: 'google/gemini-2.5-flash' OpenRouter par ekदम free aur sabse tez model hai.
        # Agar aapko gpt-3.5 hi chahiye toh badal sakte ho, par flash timeout nahi karega.
        completion = client.chat.completions.create(
            model="google/gemini-2.5-flash", 
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return completion.choices[0].message.content

    except Exception as e:
        print(f"--- CRITICAL ERROR LOG: {e} ---")
        return f"Error generating response: {e}"