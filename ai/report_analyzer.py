import google.generativeai as genai
import os
from dotenv import load_dotenv
import pytesseract
#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

load_dotenv()


from openai import OpenAI
from PIL import Image
import pytesseract
import os

#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def analyze_report(image_path, language):

    try:
        image = Image.open(image_path)

        extracted_text = pytesseract.image_to_string(image)

        prompt = f"""
        Analyze this medical report.

        Language: {language}

        Report:
        {extracted_text}

        Explain:
        1. Abnormal values
        2. Possible diseases
        3. Suggestions
        4. Simple summary
        """

        completion = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return completion.choices[0].message.content

    except Exception as e:
        return f"Error generating response: {e}"