import openai

API_KEY = "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"

openai.api_key = API_KEY


response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    temperature=0.2,
    max_tokens=1000,
    messages=[{"role": "user", "content": "Who won the 2018 FIFA world cup?"}],
)

print("response", response)

print(response["choices"][0]["message"]["content"])
