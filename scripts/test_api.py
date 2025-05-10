import openai
import os
import requests
import json

openai.api_type = "azure"
openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_BASE_URL")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")

def test_api_key():

    API_KEY = os.getenv("GEMINI_API_KEY")  # replace with your actual key
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": "hey"}
                ]
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        result = response.json()
        print("💬 Gemini Response:\n"+result['candidates'][0]['content']['parts'][0]['text'])
        return True
    else:
        False


def test_api_key2():
    try:
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        response = openai.ChatCompletion.create(
            engine=deployment_name,
            messages=[{"role": "user", "content": "Hello from GitHub Actions!"}],
            temperature=0.7,
            max_tokens=100,
        )

        print("API Response:", response.choices[0].message.content)
        return True
    except Exception as e:
        print("Error:", str(e))
        return False

if __name__ == "__main__":
    print("Testing OpenAI API key...")
    if test_api_key():
        print("✅ API key is working!")
    else:
        print("❌ API key is not working!") 