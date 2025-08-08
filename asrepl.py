from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app 
from prompt_toolkit.history import FileHistory

from rich.console import Console
from rich.markdown import Markdown

import gemini_search

help_str="""[b]Command Line LLM[/b]
commands:
<Ctrl-y> clear history
    <F1> short answers
    <F2> long answers [#777777]
   <F11> show chunks
   <F12> show history[/#777777]
"""


class AsLlm():
    def __init__(self):
        # set up prompt toolkit
        file_history = FileHistory("/tmp/.llm-history")
        self.session = PromptSession(history=file_history)
        self.kb = KeyBindings()
        self.register_keybindings()
        # set up rich console
        self.console = Console()

        self.llm = gemini_search.GeminiSearch()
        self.state = "std"
        self.chunks = []

        self.console.print(help_str)


    def register_keybindings(self):
        # @self.kb.add('f11')
        # def _(event):
        #     print(self.chunks)

        @self.kb.add('f12')
        def _(event):
            print(self.llm.contents)
            print(self.llm.generate_content_config.system_instruction)

        @self.kb.add("c-y")
        def _(event):
            self.chunks = []
            self.llm.clear_contents()
            self.console.print("[on green] History deleted [/on green]", end="")

        @self.kb.add("f1")
        def _(event):
            self.state = "short"
            self.console.print("[on green] short [/on green]", end="")
            self.llm.update_system_instruction("answer short and precise, don't explain, just answer the question")

        @self.kb.add("f2")
        def _(event):
            self.state = "std"
            self.console.print("[on green] std [/on green]", end="")
            self.llm.update_system_instruction("")


    def process_prompt(self, prompt):        
        model_output = ""
        num_dots = 0
        for chunk in self.llm.generate(prompt):
            self.chunks += chunk
            model_output += chunk.text
            self.console.print("\r[on green]" + " ", end="")
            num_dots += 1
        
        self.console.print("\r[on green]" + " " * (self.console.width - num_dots) + "[/on green]")
        self.console.print(Markdown(model_output))
        print()


    def run(self):
        while True:
            try:
                prompt = self.session.prompt(f'{self.state}> ', key_bindings=self.kb)
                if prompt.strip().lower() == 'exit':
                    break
                
                if len(prompt.strip()) == 0:
                    continue
                
                self.process_prompt(prompt)
                            
            except (KeyboardInterrupt):
                continue

            except (EOFError):
                break


if __name__ == '__main__':
    AsLlm().run()
