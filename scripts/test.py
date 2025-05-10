import openai
import os

openai.api_type = "azure"
openai.api_key = 'c70a2f4f42994598874b97ef7a945b40'
openai.api_base = 'https://risha-openai.openai.azure.com/'
openai.api_version = '2024-02-01'

# const apiType = 'azure';
# const apiKey = 'c70a2f4f42994598874b97ef7a945b40';
# const apiBase = 'https://risha-openai.openai.azure.com/';
# const apiVersion = '2024-02-01';
# const deploymentName = 'trial2'; 
def test_api_key():
    try:
        deployment_name = 'trial2'
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