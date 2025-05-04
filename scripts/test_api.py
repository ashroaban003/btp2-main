import openai
import os

openai.api_type = "azure"
openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_BASE_URL")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")


def test_api_key():
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