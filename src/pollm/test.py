import polib
from pollm.prompt_utils import PromptManager
from pollm.glossary import search_glossary
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

po = polib.pofile("src/example/mapping.po")

client = OpenAI(
    api_key="Ollama",
    # api_key=os.getenv("OPENAI_API_KEY"),
    base_url="http://localhost:11434/v1",
)

# for entry in po.untranslated_entries():
messages = [
    {
        "role": "system",
        "content": PromptManager.get_prompt("system_prompt.txt"),
    },
]
for entry in po.fuzzy_entries():
# for entry in po.untranslated_entries():
    message = {
        "role": "user",
        "content": PromptManager.get_prompt("translate.txt").format(entry=entry.msgid, dictionary=search_glossary(entry.msgid)),
    }
    print(message)
    response = client.chat.completions.create(
        messages=messages[-4:] + [message],
        model="qwen2.5:14b",
        # model="gpt-4o-mini",
        temperature=0.1,
    )
    entry.msgstr = response.choices[0].message.content
    messages.append({
        "role": "user",
        "content": entry.msgstr,
    })
    

po.save()
