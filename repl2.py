################################################################################
#               https://ai.google.dev/gemini-api/docs                          #
################################################################################
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app 
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style      
from prompt_toolkit.formatted_text import FormattedText as FT                                                                    
from prompt_toolkit.completion import PathCompleter

from rich.console import Console
from rich.markdown import Markdown

import os, sys, subprocess, mimetypes
import tempfile
import gemini_search



help_str="""**Command Line LLM**  
`<F2>`     Toggle Standard/Short Answer  
`<F3>`     Toggle Google Search  
`<F4>`     Toggle Url Context  
`<Ctrl-q>` Clear Chat History  
`<Ctrl-d>` Exit   (or type exit)  
"""

instruction_dict = { "short": 'answer short and precise, do not explain, just answer the question. If the prompt starts with "exp", give a detailed answer with explanation.', }

allowed_mimetypes = (
            'text/',
            'application/pdf',
            "image/png", "image/jpeg", "image/webp", "image/heic", "image/heif",
            "video/mp4", "video/mpeg", "video/mov", "video/avi", "video/x-flv", "video/mpg", "video/webm", "video/wmv", "video/3gpp",
            "audio/wav", "audio/mp3", "audio/aiff", "audio/aac", "audio/ogg", "audio/flac", "audio/mpeg",
        )


class Model:
    def __init__(self):
        self.data = []

    def add_item(self, item):
        self.data.append(item)
        print(f"Model: Added '{item}'")

    def get_items(self):
        return self.data


class View:
    def __init__(self) -> None:
        # set up prompt toolkit
        file_history = FileHistory(f"{tempfile.gettempdir()}/.llm-history")
        self.session = PromptSession(history=file_history)
        self.completer = PathCompleter()
        self.kb = KeyBindings()
        # set up rich console
        self.console = Console()


    def show_items(self, items):
        print("\nView: Current Items:")
        if items:
            for item in items:
                print(f"- {item}")
        else:
            print("No items to display.")

    def get_user_input(self, prompt):
        prompt = self.session.prompt(f'prompt> ', 
                                     style=Style.from_dict({'bottom-toolbar': "#1C2B16 bg:#00ff44"}), 
                                     key_bindings=self.kb,
                                     completer=self.completer,
                                     complete_while_typing=True,
                                     bottom_toolbar=self.make_bottom_toolbar,
                                     )
        return prompt


    def make_bottom_toolbar(self):
        toolbar_string = f'  {"std  " if self.state == "std" else "short"}   {"google   " if self.llm.tool_state["google_search"] else "no google"}   {"url context   "  if self.llm.tool_state["url_context"] else "no url context"}   {"chat is empty" if not self.llm.contents else "has history"}\n'
        toolbar_string += '<style bg="#aaaaaa">  F2      F3          F4               Ctrl-q   </style>'
        return HTML(toolbar_string)


class Controller:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.register_keybindings()

        self.llm = gemini_search.GeminiSearch()
        self.state = "std"
        self.state_google = "google"
        self.chunks = []


    def register_keybindings(self):
        @view.kb.add("c-q")
        def _(event):
            self.chunks = []
            self.llm.clear_contents()

        @view.kb.add("f2")
        def _(event):
            if self.state == "short":
                self.state = "std"
                self.llm.update_system_instruction("")
            else:
                self.state = "short"
                self.llm.update_system_instruction(instruction_dict["short"])

        @view.kb.add("f3")
        def _(event):
            self.llm.toggle_tool("google_search")

        @view.kb.add("f4")
        def _(event):
            self.llm.toggle_tool("url_context")


    def run(self):
        self.view.console.print(Markdown(help_str))
        
        while True:
            try:
                TODO
                                             )
                if prompt.strip().lower() in ['exit', 'quit']:
                    break
                
                if len(prompt.strip()) == 0:
                    continue

                file_name = self.is_prompt_filename(prompt)
                if file_name != "":
                    mime_type_tuple = mimetypes.guess_type(file_name)
                    if self.is_file_allowed(mime_type_tuple):
                        self.console.print(f"[#00ff44]file accepted[/#00ff44]")
                        self.llm.add_file_to_content(file_name)
                        continue
                    else:
                        self.console.print(f"[#ff4400]file rejected, it has non allowed mimetype:[/#ff4400] {mime_type_tuple[0]}")
                        continue

                self.process_prompt(prompt)
                            
            except (KeyboardInterrupt):
                continue

            except (EOFError):
                break



if __name__ == "__main__":
    model = Model()
    view = View()
    controller = Controller(model, view)
    controller.run()
