import typer
from types import SimpleNamespace

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    pinboard_token: str = typer.Option(None, envvar="PINBOARD_TOKEN"),
):
    # if not pinboard_token:
    #     print(
    #         "Missing pinboard token; pass --pinboard-token or set env[PINBOARD_TOKEN]"
    #     )
    #     raise typer.Exit(1)
    ctx.obj = SimpleNamespace(pinboard_token = pinboard_token)
    if ctx.invoked_subcommand is None:
        print("""
   ___  ____  __   __   __  ___
  / _ \/ __ \/ /  / /  /  |/  /
 / ___/ /_/ / /__/ /__/ /|_/ / 
/_/   \____/____/____/_/  /_/  
          """)


# @app.command()
# def all(ctx: typer.Context):
#     # do something with ctx.obj.pinboard_token
#     ...


# @app.command()
# def new(ctx: typer.Context):
#     # do something with ctx.obj.pinboard_token
#     ...


if __name__ == "__main__":
    app()