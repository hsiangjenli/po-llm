import asyncio
from agent_framework.openai import OpenAIResponsesClient
from agent_framework import ChatMessage, ChatAgent
from agent_framework.devui import serve

from pollm.glossary import search_glossary
from pollm.po_utils import load_po_file, save_po_file
import polib
import dotenv
import os

dotenv.load_dotenv()

import subprocess


def wrap_po_file():
    """Run wrap on the current directory."""
    subprocess.run(["uvx", "powrap", "--modified"], check=True)


def translate_text(query: str) -> str:
    """Translate the given text using the glossary."""
    # This is a placeholder; actual translation would use the agent
    return query  # For now, just return the query


def list_untranslated_entries(file_path: str) -> list[dict]:
    """List untranslated entries in a PO file given its path."""
    po = polib.pofile(file_path)
    return [e.__dict__ for e in po if not e.translated()]


agent = ChatAgent(
    name="PO File Translator",
    chat_client=OpenAIResponsesClient(
        model_id="gpt-5-mini-2025-08-07", api_key=os.getenv("OPENAI_API_KEY")
    ),
    tools=[
        search_glossary,
        wrap_po_file,
        list_untranslated_entries,
        translate_text,
        load_po_file,
        save_po_file,
    ],
)

if __name__ == "__main__":
    serve([agent], auto_open=True)
