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


class AsLlm():
    def __init__(self):
        # set up prompt toolkit
        file_history = FileHistory(f"{tempfile.gettempdir()}/.llm-history")
        self.session = PromptSession(history=file_history)
        self.completer = PathCompleter()
        self.kb = KeyBindings()
        self.register_keybindings()
        # set up rich console
        self.console = Console()

        self.llm = gemini_search.GeminiSearch()
        self.state = "std"
        self.state_google = "google"
        self.chunks = []


    def register_keybindings(self):
        @self.kb.add('f10')
        def _(event):
            print(self.chunks)

        @self.kb.add('f12')
        def _(event):
            print(self.llm.contents)

        @self.kb.add("c-q")
        def _(event):
            self.chunks = []
            self.llm.clear_contents()

        @self.kb.add("f2")
        def _(event):
            if self.state == "short":
                self.state = "std"
                self.llm.update_system_instruction("")
            else:
                self.state = "short"
                self.llm.update_system_instruction(instruction_dict["short"])

        @self.kb.add("f3")
        def _(event):
            self.llm.toggle_tool("google_search")

        @self.kb.add("f4")
        def _(event):
            self.llm.toggle_tool("url_context")


    def process_prompt(self, prompt):        
        model_output = ""
        grounding_chunks = []
        url_metadata = []
        num_dots = 0
        for chunk in self.llm.generate(prompt):
            self.chunks += chunk
            if type(chunk.text)==str:
                model_output += chunk.text
            
            if self.llm.tool_state['google_search']:
                # if chunk.candidates[0].grounding_metadata.grounding_chunks:
                if chunk.candidates and chunk.candidates[0].grounding_metadata and chunk.candidates[0].grounding_metadata.grounding_chunks:
                    grounding_chunks += chunk.candidates[0].grounding_metadata.grounding_chunks
            
            if self.llm.tool_state['url_context']:
                if chunk.candidates and chunk.candidates[0].url_context_metadata and chunk.candidates[0].url_context_metadata.url_metadata:
                    url_metadata += chunk.candidates[0].url_context_metadata.url_metadata
            
            self.console.print("\r[#00ff00]" + "-", end="")
            num_dots += 1

        self.console.print("\r[#00ff00]" + "-" * (self.console.width - num_dots) + "[/#00ff00]")
        self.console.print(Markdown(model_output))
        
        link_list = [f"[{link.web.title}]({link.web.uri}) " for link in grounding_chunks]
        link_string = " ".join(link_list)
        self.console.print(Markdown(link_string))

        link_list = [f"[{entry.retrieved_url}]({entry.retrieved_url}) " for entry in url_metadata]
        link_string = " ".join(link_list)
        self.console.print(Markdown(link_string))

        self.llm.add_content(role="model", text=model_output)


    def make_bottom_toolbar(self):
        toolbar_string = f'  {"std  " if self.state == "std" else "short"}   {"google   " if self.llm.tool_state["google_search"] else "no google"}   {"url context   "  if self.llm.tool_state["url_context"] else "no url context"}   {"chat is empty" if not self.llm.contents else "has history"}\n'
        toolbar_string += '<style bg="#aaaaaa">  F2      F3          F4               Ctrl-q   </style>'
        return HTML(toolbar_string)


    def is_prompt_filename(self, prompt):
        if os.path.isfile(prompt.strip()):
            #self.console.print("file detected", end=" | ")
            file_name = prompt.strip()
            return file_name
        
        if os.path.isfile(prompt.strip()[1:-1]):
            #self.console.print("file with '' detected", end=" | ")
            file_name = prompt.strip()[1:-1]
            return file_name

        if sys.platform == "win32":
            try:
                win_path = subprocess.run(f"cygpath -w {prompt.strip()}", capture_output=True, text=True).stdout[:-1]
                
                if os.path.isfile(win_path):
                    #self.console.print("win file detected", end=" | ")
                    file_name = prompt.strip()
                    return win_path
            except:
                pass

        return ""


    def is_file_allowed(self, mime_type_tuple):
        if type(mime_type_tuple[0]) == str:
            for entry in allowed_mimetypes:
                if entry in mime_type_tuple[0]:
                    return True
        return False


    def run(self):
        self.console.print(Markdown(help_str))
        
        while True:
            try:
                prompt = self.session.prompt(f'prompt> ', 
                                             style=Style.from_dict({'bottom-toolbar': "#1C2B16 bg:#00ff44"}), 
                                             key_bindings=self.kb,
                                             completer=self.completer,
                                             complete_while_typing=True,
                                             bottom_toolbar=self.make_bottom_toolbar,
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


def main(argv):
    if len(argv) == 1:
        AsLlm().run()
    else:
        _, *prompt = argv
        prompt = " ".join(prompt)
        a = AsLlm()
        a.console.print(prompt)
        a.process_prompt(prompt)


if __name__ == '__main__':
    main(sys.argv)
