import typer

app = typer.Typer()


@app.command("fuzzy")
def cli_po_fuzzy(): ...


@app.command("translate")
def cli_po_translate(): ...


if __name__ == "__main__":
    app()
