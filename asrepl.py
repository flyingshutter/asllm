from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app 
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style      
from prompt_toolkit.formatted_text import FormattedText as FT                                                                    

from rich.console import Console
from rich.markdown import Markdown

import tempfile
import gemini_search

help_str="""**Command Line LLM**  
`<F1>`     Toggle Standard/Short Answer  
`<F3>`     Toggle Google Search  
`<Ctrl-q>` Clear Chat History  
`<Ctrl-d>` Exit   (or type exit)  
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

        @self.kb.add("c-q")
        def _(event):
            self.chunks = []
            self.llm.clear_contents()

        @self.kb.add("f1")
        def _(event):
            if self.state == "short":
                self.state = "std"
                self.llm.update_system_instruction("")
            else:
                self.state = "short"
                self.llm.update_system_instruction("answer short and precise, don't explain, just answer the question")

        @self.kb.add("f3")
        def _(event):
            if not self.state_google:
                self.state_google = "google"
                self.llm.switch_google_search(True)
            else:
                self.state_google = ""
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


    def make_bottom_toolbar(self):
        toolbar_string = f'    {"std  " if self.state == "std" else "short"}           {"google   " if self.state_google else "no google"}                 {"chat history is empty" if not self.llm.contents else ""}\n'
        toolbar_string += '<style bg="#aaaaaa">F1: short/std   F3: google on/off     Ctrl-q: clear chat history😀   </style>'
        return HTML(toolbar_string)


    def run(self):
        while True:
            try:
                prompt = self.session.prompt(f'prompt> ', 
                                             style=Style.from_dict({'bottom-toolbar': "#1C2B16 bg:#00ff44"}), 
                                             key_bindings=self.kb,
                                             bottom_toolbar=self.make_bottom_toolbar)
                if prompt.strip().lower() in ['exit', 'quit']:
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
