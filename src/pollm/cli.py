import os
from pathlib import Path

import polib
import tqdm
import typer
from openai import OpenAI

from pollm.glossary import search_glossary
from pollm.prompt_utils import PromptManager
from pollm.agent import IterativeTranslationAgent, MCPTranslationTool

# Init ------------------------------------------------------------------------------------------- #
app = typer.Typer()

# Set up OpenRouter authentication
api_key = os.getenv("POLLM_OPENAI_API_KEY")
base_url = os.getenv("POLLM_BASE_URL", "https://openrouter.ai/api/v1")

kwargs = {"api_key": api_key, "base_url": base_url}

client = OpenAI(**kwargs)

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
    model: str = "qwen/qwen-2.5-72b-instruct:free",  # OpenRouter model name
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
    model: str = typer.Option("qwen/qwen-2.5-72b-instruct:free", help="Model to use for translation"),
    temperature: float = typer.Option(0.1, help="Temperature for the model"),
    max_messages: int = typer.Option(
        4, help="Maximum number of messages to send to the model"
    ),
    translate_mode: str = typer.Option(
        "fully", help="Translation mode, options: fully, untranslated"
    ),
):
    """處理 PO 檔案中被標記為 fuzzy 的項目，使用 LLM 模型進行翻譯，並移除 fuzzy 標記.

    .. code-block:: shell

        pollm fuzzy <pofile> --model <model> --temperature <temperature> --max_messages <max_messages> --translate_mode <translate_mode>

    Args:
        pofile (Path): PO 檔案的路徑
        model (str): 使用的模型名稱
        temperature (float): 控制模型輸出的隨機程度
        max_messages (int): 提供給模型的對話歷史訊息數量
        translate_mode (str): 翻譯模式，可選 "fully" 或 "untranslated"
    """
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

        messages.extend([
            {"role": "user", "content": entry.msgid},
            {"role": "assistant", "content": entry.msgstr}
        ])

    po.save()


@app.command("translate")
def cli_po_translate(
    pofile: Path = typer.Argument(..., help="Path to the PO file"),
    model: str = typer.Option("qwen/qwen-2.5-72b-instruct:free", help="Model to use for translation"),
    temperature: float = typer.Option(0.1, help="Temperature for the model"),
    max_messages: int = typer.Option(
        4, help="Maximum number of messages to send to the model"
    ),
    translate_mode: str = typer.Option(
        "fully", help="Translation mode, options: fully, untranslated"
    ),
):
    """處理 PO 檔案中未翻譯的項目，使用 LLM 模型進行翻譯.

    .. code-block:: shell

        pollm translate <pofile> --model <model> --temperature <temperature> --max_messages <max_messages> --translate_mode <translate_mode>

    Args:
        pofile (Path): PO 檔案的路徑
        model (str): 使用的模型名稱
        temperature (float): 控制模型輸出的隨機程度
        max_messages (int): 提供給模型的對話歷史訊息數量
        translate_mode (str): 翻譯模式，可選 "fully" 或 "untranslated"
    """
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

        messages.extend([
            {"role": "user", "content": entry.msgid},
            {"role": "assistant", "content": entry.msgstr}
        ])

    po.save()


@app.command("agent")
def cli_agent_translate(
    pofile: Path = typer.Argument(..., help="Path to the PO file"),
    model: str = typer.Option("qwen/qwen-2.5-72b-instruct:free", help="Model to use for translation"),
    temperature: float = typer.Option(0.1, help="Temperature for the model"),
    max_iterations: int = typer.Option(3, help="Maximum iterations per translation"),
    target_entries: str = typer.Option("untranslated", help="Target entries: untranslated, fuzzy, all"),
    auto_confirm: bool = typer.Option(False, help="Auto-confirm high confidence translations"),
    confidence_threshold: float = typer.Option(0.8, help="Confidence threshold for auto-confirmation"),
    context_file: Path = typer.Option(None, help="Path to save/load translation context"),
):
    """Interactive AI agent for iterative contextual translation.
    
    This command implements an iterative translation workflow that:
    - Uses MCP-style tools to search for suitable translations
    - Provides interactive confirmation and refinement capabilities
    - Maintains context across translation iterations
    - Learns from user feedback to improve subsequent translations
    
    .. code-block:: shell
    
        pollm agent <pofile> --model <model> --max_iterations 3 --auto_confirm
    
    Args:
        pofile (Path): PO file path
        model (str): LLM model name
        temperature (float): Model temperature for creativity
        max_iterations (int): Maximum refinement iterations per entry
        target_entries (str): Which entries to process (untranslated/fuzzy/all)
        auto_confirm (bool): Auto-confirm translations above confidence threshold
        confidence_threshold (float): Threshold for auto-confirmation (0.0-1.0)
        context_file (Path): File to persist translation context between sessions
    """
    
    # Initialize MCP tool and agent
    mcp_tool = MCPTranslationTool()
    agent = IterativeTranslationAgent(
        client=client,
        prompt_manager=PromptManager(),
        mcp_tool=mcp_tool,
        max_iterations=max_iterations,
        confidence_threshold=confidence_threshold
    )
    
    # Load previous context if available
    if context_file and context_file.exists():
        print(f"Loading translation context from {context_file}")
        agent.load_session_context(context_file)
    
    print(f"Starting iterative translation with AI agent...")
    print(f"Model: {model}")
    print(f"Max iterations per entry: {max_iterations}")
    print(f"Target entries: {target_entries}")
    print(f"Auto-confirm threshold: {confidence_threshold}")
    print(f"Interactive mode: {'No' if auto_confirm else 'Yes'}")
    
    # Process the PO file
    results = agent.process_po_file(
        po_file_path=pofile,
        model=model,
        temperature=temperature,
        auto_confirm=auto_confirm,
        target_entries=target_entries
    )
    
    # Save context if specified
    if context_file:
        agent.save_session_context(context_file)
        print(f"Translation context saved to {context_file}")
    
    # Print results summary
    print(f"\n{'='*50}")
    print("TRANSLATION SUMMARY")
    print(f"{'='*50}")
    print(f"Processed entries: {results['processed']}")
    print(f"Accepted translations: {results['accepted']}")
    print(f"Skipped entries: {results['skipped']}")
    print(f"Failed entries: {results['failed']}")
    print(f"Total iterations used: {results['total_iterations']}")
    
    if results['processed'] > 0:
        avg_iterations = results['total_iterations'] / results['processed']
        print(f"Average iterations per entry: {avg_iterations:.1f}")
        success_rate = results['accepted'] / results['processed'] * 100
        print(f"Success rate: {success_rate:.1f}%")


if __name__ == "__main__":
    app()
