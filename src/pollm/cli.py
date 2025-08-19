import os
from pathlib import Path
import time

import polib
import tqdm
import typer
from openai import OpenAI

from pollm.glossary import search_glossary
from pollm.prompt_utils import PromptManager
from pollm.batch_translator import BatchTranslator

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


@app.command("translate-batch")
def cli_po_translate_batch(
    pofile: Path = typer.Argument(..., help="Path to the PO file"),
    model: str = typer.Option("qwen/qwen-2.5-72b-instruct:free", help="Model to use for translation"),
    temperature: float = typer.Option(0.1, help="Temperature for the model"),
    batch_size: int = typer.Option(50, help="Number of entries to process in each batch"),
    translate_mode: str = typer.Option(
        "untranslated", help="Translation mode, options: fully, untranslated, fuzzy"
    ),
    max_context_pairs: int = typer.Option(20, help="Maximum number of translation pairs to keep as context"),
):
    """處理 PO 檔案使用批次翻譯以優化 token 使用量.

    .. code-block:: shell

        pollm translate-batch <pofile> --batch-size 50 --translate_mode untranslated

    Args:
        pofile (Path): PO 檔案的路徑
        model (str): 使用的模型名稱
        temperature (float): 控制模型輸出的隨機程度
        batch_size (int): 每批處理的項目數量
        translate_mode (str): 翻譯模式，可選 "fully", "untranslated", "fuzzy"
        max_context_pairs (int): 保留作為上下文的翻譯對數量
    """
    po = polib.pofile(pofile)
    
    # Select entries based on mode
    if translate_mode == "fully":
        entries = list(po)
    elif translate_mode == "untranslated":
        entries = po.untranslated_entries()
    elif translate_mode == "fuzzy":
        entries = po.fuzzy_entries()
    else:
        typer.echo(f"Unknown translate_mode: {translate_mode}")
        raise typer.Exit(1)
    
    if not entries:
        typer.echo(f"No entries to process for mode: {translate_mode}")
        return
    
    typer.echo(f"Found {len(entries)} entries to process")
    
    # Initialize batch translator
    batch_translator = BatchTranslator(
        client=client,
        model=model,
        temperature=temperature,
        max_context_pairs=max_context_pairs
    )
    batch_translator.set_glossary_function(search_glossary)
    
    # Process in batches
    total_batches = (len(entries) + batch_size - 1) // batch_size
    processed_count = 0
    
    start_time = time.time()
    
    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(entries))
        batch_entries = entries[start_idx:end_idx]
        
        typer.echo(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_entries)} entries)")
        
        # Determine prompt type based on translate_mode
        prompt_type = "fuzzy" if translate_mode == "fuzzy" else "translate"
        
        # Translate batch
        batch_results = batch_translator.translate_batch(batch_entries, prompt_type)
        
        # Apply results
        for local_idx, entry in enumerate(batch_entries):
            if local_idx in batch_results and batch_results[local_idx]:
                old_msgstr = entry.msgstr
                entry.msgstr = batch_results[local_idx]
                
                # Remove fuzzy flag if this was a fuzzy translation
                if translate_mode == "fuzzy" and "fuzzy" in entry.flags:
                    entry.flags.remove("fuzzy")
                
                processed_count += 1
        
        # Show progress
        progress = (batch_idx + 1) / total_batches * 100
        typer.echo(f"Progress: {progress:.1f}% ({processed_count} translations applied)")
    
    # Save the file
    po.save()
    
    # Show statistics
    end_time = time.time()
    total_time = end_time - start_time
    cache_stats = batch_translator.cache.get_stats()
    
    typer.echo("\n" + "="*50)
    typer.echo("BATCH TRANSLATION COMPLETED")
    typer.echo("="*50)
    typer.echo(f"Total entries processed: {processed_count}")
    typer.echo(f"Total time: {total_time:.2f} seconds")
    typer.echo(f"Average time per entry: {total_time/len(entries):.3f} seconds")
    typer.echo(f"Cache hit rate: {cache_stats['hit_rate']:.1f}%")
    typer.echo(f"Cache hits: {cache_stats['hits']}")
    typer.echo(f"Cache misses: {cache_stats['misses']}")
    typer.echo(f"Cache size: {cache_stats['cache_size']} entries")
    typer.echo(f"Total API calls: {total_batches} (vs {len(entries)} for individual processing)")
    
    if len(entries) > 0:
        api_reduction = (1 - total_batches / len(entries)) * 100
        typer.echo(f"API call reduction: {api_reduction:.1f}%")


if __name__ == "__main__":
    app()
