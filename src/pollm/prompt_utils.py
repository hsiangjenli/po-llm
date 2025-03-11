import os


class PromptManager:
    _prompt_dir = os.path.join(os.path.dirname(__file__), "prompts")

    @classmethod
    def list(cls) -> list:
        instance = cls()
        return os.listdir(instance._prompt_dir)

    @classmethod
    def get_prompt(cls, prompt_path):
        instance = cls()
        with open(
            os.path.join(instance._prompt_dir, prompt_path), "r", encoding="utf-8"
        ) as f:
            return f.read()


if __name__ == "__main__":
    print(PromptManager.get_prompt("system_prompt.txt"))
    print(PromptManager.list())
