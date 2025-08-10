from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app 
from prompt_toolkit.history import FileHistory

from rich.console import Console
from rich.markdown import Markdown

import tempfile
import gemini_search

help_str="""**Command Line LLM**  
`<Ctrl-y>` Clear History  
`<Ctrl-d>` Exit  
`<F1>`     Short Answers  
`<F2>`     Long Answers  
`<F3>`     Toggle Google Search  
`<F10>`    Show Chunks  
`<F12>`    Show History
"""


class AsLlm():
    def __init__(self):
        # set up prompt toolkit
        file_history = FileHistory(f"{tempfile.gettempdir()}/.llm-history")
        self.session = PromptSession(history=file_history)
        self.kb = KeyBindings()
        self.register_keybindings()
        # set up rich console
        self.console = Console()

        self.llm = gemini_search.GeminiSearch()
        self.state = "std"
        self.state_google = "google"
        self.chunks = []

        self.console.print(Markdown(help_str))


    def register_keybindings(self):
        @self.kb.add('f10')
        def _(event):
            print(self.chunks)

        @self.kb.add('f12')
        def _(event):
            print(self.llm.contents)
            print(self.llm.generate_content_config.system_instruction)

        @self.kb.add("c-y")
        def _(event):
            self.chunks = []
            self.llm.clear_contents()
            self.console.print("[on #003300] History deleted [/on #003300]", end="")

        @self.kb.add("f1")
        def _(event):
            self.state = "short"
            self.console.print("[on #003300] short [/on #003300]", end="")
            self.llm.update_system_instruction("answer short and precise, don't explain, just answer the question")

        @self.kb.add("f2")
        def _(event):
            self.state = "std"
            self.console.print("[on #003300] std [/on #003300]", end="")
            self.llm.update_system_instruction("")


        @self.kb.add("f3")
        def _(event):
            if not self.state_google:
                self.state_google = "google"
                self.console.print("[on #003300] google [/on #003300]", end="")
                self.llm.switch_google_search(True)
            else:
                self.state_google = ""
                self.console.print("[on #003300] no google [/on #003300]", end="")
                self.llm.switch_google_search(False)


    def process_prompt(self, prompt):        
        model_output = ""
        grounding_chunks = []
        num_dots = 0
        for chunk in self.llm.generate(prompt):
            self.chunks += chunk
            if type(chunk.text)==str:
                model_output += chunk.text
            
            if self.state_google:
                if chunk.candidates[0].grounding_metadata.grounding_chunks:
                    grounding_chunks += chunk.candidates[0].grounding_metadata.grounding_chunks
            
            self.console.print("\r[on #003300]" + " ", end="")
            num_dots += 1

        self.console.print("\r[on #003300]" + " " * (self.console.width - num_dots) + "[/on #003300]")
        self.console.print(Markdown(model_output))
        
        link_list = [f"[{chunk.web.title}]({chunk.web.uri}) " for chunk in grounding_chunks]
        link_string = " ".join(link_list)
        self.console.print(Markdown(link_string))

        self.llm.add_content(role="model", text=model_output)


    def run(self):
        while True:
            try:
                prompt = self.session.prompt(f'{self.state} {self.state_google}> ', key_bindings=self.kb)
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
