from pathlib import Path

import polib
import tqdm
import typer
from openai import OpenAI

from pollm.glossary import search_glossary
from pollm.prompt_utils import PromptManager

# Init ------------------------------------------------------------------------------------------- #
app = typer.Typer()

client = OpenAI(api_key="Ollama", base_url="http://localhost:11434/v1")

messages = [
    {
        "role": "system",
        "content": PromptManager.get_prompt("system_prompt.txt"),
    },
]


# Function --------------------------------------------------------------------------------------- #
def prompt_message(prompt: str, entry: polib.POEntry):
    return {
        "role": "user",
        "content": PromptManager.get_prompt(prompt).format(
            entry=entry.msgid, dictionary=search_glossary(entry.msgid)
        ),
    }


def response_msgstr(
    entry: polib.POEntry,
    messages: list,
    client: OpenAI,
    prompt: str = "translate.txt",
    max_messages: int = 4,
    model: str = "qwen2.5:14b",
    temperature: float = 0.1,
):
    response = client.chat.completions.create(
        messages=messages[-max_messages:]
        + [prompt_message(prompt=prompt, entry=entry)],
        model=model,
        temperature=temperature,
    )
    return response.choices[0].message.content


# Command ---------------------------------------------------------------------------------------- #
@app.command("fuzzy")
def cli_po_fuzzy(
    pofile: Path = typer.Argument(..., help="Path to the PO file"),
    model: str = typer.Option("qwen2.5:14b", help="Model to use for translation"),
    temperature: float = typer.Option(0.1, help="Temperature for the model"),
    max_messages: int = typer.Option(
        4, help="Maximum number of messages to send to the model"
    ),
    translate_mode: str = typer.Option(
        "fully", help="Translation mode, options: fully, untranslated"
    ),
):
    po = polib.pofile(pofile)
    entries = po if translate_mode == "fully" else po.fuzzy_entries()

    for entry in tqdm.tqdm(entries):
        if "fuzzy" in entry.flags:
            entry.msgstr = response_msgstr(
                entry=entry,
                messages=messages[:-max_messages],
                client=client,
                prompt="fuzzy.txt",
                model=model,
                temperature=temperature,
            )
            entry.flags.remove("fuzzy")

        messages.append(
            {
                "role": "user",
                "content": entry.msgstr,
            }
        )

    po.save()


@app.command("translate")
def cli_po_translate(
    pofile: Path = typer.Argument(..., help="Path to the PO file"),
    model: str = typer.Option("qwen2.5:14b", help="Model to use for translation"),
    temperature: float = typer.Option(0.1, help="Temperature for the model"),
    max_messages: int = typer.Option(
        4, help="Maximum number of messages to send to the model"
    ),
    translate_mode: str = typer.Option(
        "fully", help="Translation mode, options: fully, untranslated"
    ),
):
    po = polib.pofile(pofile)
    entries = po if translate_mode == "fully" else po.untranslated_entries()

    for entry in tqdm.tqdm(entries):
        if entry.msgstr == "":
            entry.msgstr = response_msgstr(
                entry=entry,
                messages=messages[:-max_messages],
                client=client,
                prompt="translate.txt",
                model=model,
                temperature=temperature,
            )

        messages.append(
            {
                "role": "user",
                "content": entry.msgstr,
            }
        )

    po.save()


if __name__ == "__main__":
    app()
