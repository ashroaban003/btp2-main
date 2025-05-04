import openai
import os

def test_api_key():
    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API key is working' if you can read this."}
            ]
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