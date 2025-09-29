################################################################################
#               https://ai.google.dev/gemini-api/docs                          #
################################################################################
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import PathCompleter

from rich.console import Console
from rich.markdown import Markdown

from typing import Optional
from abc import ABC, abstractmethod
import enum
import sys
import json, re
import tempfile
import gemini_search, filehandling

help_str=r"""**Command Line LLM**  
read youtube videos from url, pdf/image/video/audio from filepath  
`<F2>`     Toggle Standard/Short/Custom Answer  
`<F3>`     Toggle Google Search  
`<F4>`     Toggle Url Context  
`<F5>`     Toggle Gemini Models (pro, flash, flash_lite)  
`<Ctrl-q>` Clear Chat History  
`<Ctrl-d>` Exit (or type exit)  
`\`        Enter custom system instruction
"""


class Llm:
    def __init__(self) -> None:
        self.gemini = gemini_search.GeminiSearch()
        self._current_model_index = 1
        self._current_instruction_index = 0
        self._instruction_list = [{"name":"std", "instruction":''},
                            {"name":"short", "instruction":'answer short and precise, do not explain, just answer the question. If the prompt starts with "exp", give a detailed answer with explanation.'},
                            {"name":"custom", "instruction":''}]

    @property
    def active_instruction(self):
        return self._instruction_list[self._current_instruction_index]

    def activate_next_instruction(self):
        self._current_instruction_index = (self._current_instruction_index + 1) % len(self._instruction_list)
        self.gemini.system_instruction = self.active_instruction["instruction"]
        return self.active_instruction

    def set_custom_instruction(self, text):
        self._instruction_list[2]["instruction"] = text
        self._current_instruction_index = 2
        self.gemini.system_instruction = self.active_instruction["instruction"]

    def activate_next_model(self):
        self._current_model_index = (self._current_model_index + 1) % len(self.gemini.known_models)
        self.gemini.model = self.gemini.known_models[self._current_model_index]()


    @property
    def use_url_context_tool(self):
        return self.gemini.tools_state["url_context"]

    @use_url_context_tool.setter
    def use_url_context_tool(self, value):
        self.gemini.tools_state["url_context"] = value


    @property
    def use_google_search_tool(self):
        return self.gemini.tools_state["google_search"]

    @use_google_search_tool.setter
    def use_google_search_tool(self, value):
        self.gemini.tools_state["google_search"] = value


    def has_history(self):
        return self.gemini.contents != []


    def clear_history(self):
        self.gemini.clear_contents()


    def ask_llm(self, prompt):
        model_output = ""
        grounding_chunks = []
        url_metadata = []
        parts = []
        for chunk in self.gemini.generate_stream(prompt):
            if type(chunk.text)==str:
                model_output += chunk.text

            if self.gemini.tools_state['google_search']:
                if chunk.candidates and chunk.candidates[0].grounding_metadata and chunk.candidates[0].grounding_metadata.grounding_chunks:
                    grounding_chunks += chunk.candidates[0].grounding_metadata.grounding_chunks

            if self.gemini.tools_state['url_context']:
                if chunk.candidates and chunk.candidates[0].url_context_metadata and chunk.candidates[0].url_context_metadata.url_metadata:
                    url_metadata += chunk.candidates[0].url_context_metadata.url_metadata

            if chunk.candidates:
                for candidate in chunk.candidates:
                    if candidate.content.parts:
                        for part in candidate.content.parts:
                            parts.append(part)

            yield {
                "model_output":model_output,
                "grounding_chunks":grounding_chunks,
                "url_metadata":url_metadata,
                "parts":parts,
                }


class RichPrinter:
    def __init__(self) -> None:
        self.console = Console()


    def print_result(self, result):
        self.console.print(Markdown(result["model_output"]))

        link_list = [f"[{link.web.title}]({link.web.uri}) " for link in result["grounding_chunks"]]
        link_string = " ".join(link_list)
        self.console.print(Markdown(link_string))

        link_list = [f"[{entry.retrieved_url}]({entry.retrieved_url}) " for entry in result["url_metadata"]]
        link_string = " ".join(link_list)
        self.console.print(Markdown(link_string))


class View:
    def __init__(self, llm: Llm) -> None:
        self.llm = llm

        # set up prompt toolkit
        file_history = FileHistory(f"{tempfile.gettempdir()}/.llm-history")
        self.session = PromptSession(history=file_history)
        self.completer = PathCompleter()
        self.kb = KeyBindings()

        self.printer = RichPrinter()

    def register_keybindings(self):
        @self.kb.add("c-q")
        def _(event):
            self.llm.gemini.clear_contents()

        @self.kb.add("f2")
        def _(event):
            active_config = self.llm.activate_next_instruction()
            # self.printer.console.print(active_config)

        @self.kb.add("f3")
        def _(event):
            self.llm.use_google_search_tool = not self.llm.use_google_search_tool

        @self.kb.add("f4")
        def _(event):
            self.llm.use_url_context_tool = not self.llm.use_url_context_tool

        @self.kb.add("f5")
        def _(event):
            self.llm.activate_next_model()


    def get_user_input(self):
        prompt = self.session.prompt(f'prompt> ',
                                     style=Style.from_dict({'bottom-toolbar': "#1C2B16 bg:#00ff44"}),
                                     key_bindings=self.kb,
                                     completer=self.completer,
                                     complete_while_typing=True,
                                     bottom_toolbar=self.make_bottom_toolbar,
                                     )
        return prompt


    def make_bottom_toolbar(self):
        answer = self.llm.active_instruction["name"].ljust(6, " ")
        toolbar_string = f'  {answer}   {"google   " if self.llm.use_google_search_tool else "no google"}   {"url context   "  if self.llm.use_url_context_tool else "no url context"}   {"has history" if self.llm.has_history() else "chat is empty"}    {self.llm.gemini.model.short_name}\n'
        toolbar_string += '<style bg="#aaaaaa">  F2       F3          F4               Ctrl-q           F5</style>'
        return HTML(toolbar_string)


#  ____                            _     _   _                 _ _
# |  _ \ _ __ ___  _ __ ___  _ __ | |_  | | | | __ _ _ __   __| | | ___ _ __ ___
# | |_) | '__/ _ \| '_ ` _ \| '_ \| __| | |_| |/ _` | '_ \ / _` | |/ _ \ '__/ __|
# |  __/| | | (_) | | | | | | |_) | |_  |  _  | (_| | | | | (_| | |  __/ |  \__ \
# |_|   |_|  \___/|_| |_| |_| .__/ \__| |_| |_|\__,_|_| |_|\__,_|_|\___|_|  |___/
#                           |_|
class Continuation(enum.Enum):
    CONTINUE = "continue_loop"
    BREAK = "break_loop"
    UNHANDLED = "undefined"


class PromptHandler(ABC):
    def __init__(self, successor:Optional['PromptHandler']=None) -> None:
        self.successor: Optional[PromptHandler] = successor

    @staticmethod
    @abstractmethod
    def _continuation() -> Continuation:
        pass

    def handle(self, prompt) -> Continuation:
        responsible = self._check_responsibility(prompt)
        if responsible:
            self._execute(prompt)
            return self._continuation()
        else:
            if self.successor:
                return self.successor.handle(prompt)
            else:
                return Continuation.UNHANDLED


    @abstractmethod
    def _check_responsibility(self, prompt: str) -> bool:
        pass

    @abstractmethod
    def _execute(self, prompt: str):
        ...


class BreakHandler(PromptHandler):
    def __init__(self, successor) -> None:
        super().__init__(successor)

    @staticmethod
    def _continuation() -> Continuation:
        return Continuation.BREAK


class ContinueHandler(PromptHandler):
    def __init__(self, successor) -> None:
        super().__init__(successor)

    @staticmethod
    def _continuation() -> Continuation:
        return Continuation.CONTINUE


class EmptyPromptHandler(ContinueHandler):
    def __init__(self, successor:Optional[PromptHandler]=None) -> None:
        super().__init__(successor)

    def _check_responsibility(self, prompt: str) -> bool:
        if len(prompt.strip()) == 0:
            return True
        return False

    def _execute(self, prompt: str):
        pass


class ExitHandler(BreakHandler):
    def __init__(self, successor:Optional[PromptHandler]=None) -> None:
        super().__init__(successor)

    def _check_responsibility(self, prompt: str) -> bool:
        if prompt.strip().lower() in ["exit", "quit"]:
            return True
        return False

    def _execute(self, prompt):
        pass


class YoutubeUrlHandler(ContinueHandler):
    def __init__(self, llm, view, successor:Optional[PromptHandler]=None) -> None:
        super().__init__(successor)
        self.llm = llm
        self.view = view

    def _check_responsibility(self, prompt: str) -> bool:
        if url := filehandling.YoutubeValidator().validate(prompt):
            return True
        return False

    def _execute(self, prompt):
        url = filehandling.YoutubeValidator().get_url(prompt)
        self.llm.gemini.add_youtube_video_to_content(url)
        self.view.printer.console.print(f"[#00ff44]youtube video accepted[/#00ff44]")


class FileHandler(ContinueHandler):
    def __init__(self, llm, view, file_loader: filehandling.FileLoader, successor: Optional[PromptHandler] = None) -> None:
        super().__init__(successor)
        self.llm = llm
        self.view = view
        self.file_loader = file_loader

    def _check_responsibility(self, prompt: str) -> bool:
        file_data = self.file_loader.validate(prompt)
        return True if file_data else False

    def _execute(self, prompt: str):
        file_name = self.file_loader.validate(prompt)
        mimetype = self.file_loader.get_mimetype(file_name)
        if mimetype not in gemini_search.allowed_mimetypes:
            self.view.printer.console.print(f"[#ff4400]file rejected, it has non allowed mimetype:[/#ff4400] {mimetype}")
        else:
            bin_data = self.file_loader.load(file_name)
            self.view.printer.console.print(f"[#00ff44]file accepted[/#00ff44]")
            self.llm.gemini.add_file_to_content(bin_data, mimetype)


class DefaultHandler(ContinueHandler):
    def __init__(self, llm, view, successor: Optional[PromptHandler] = None) -> None:
        super().__init__(successor)
        self.llm = llm
        self.view = view

    def _check_responsibility(self, prompt: str) -> bool:
        return True

    def _execute(self, prompt):
        num_dots = 0
        result = {}
        for result in self.llm.ask_llm(prompt):
            self.view.printer.console.print("\r[#00ff00]" + "-", end="")
            num_dots += 1

        self.view.printer.console.print("\r[#00ff00]" + "-" * (self.view.printer.console.width - num_dots) + "[/#00ff00]")

        if result:
            self.view.printer.print_result(result)
            self.llm.gemini.add_content(role="model", text=result["model_output"])
            embedded_json_dicts = JsonExtractor().extract(result["model_output"])
            print(embedded_json_dicts)

#  ____  _____ ____  _
# |  _ \| ____|  _ \| |
# | |_) |  _| | |_) | |
# |  _ <| |___|  __/| |___
# |_| \_\_____|_|   |_____|
class ReplController:
    def __init__(self):
        self.llm = Llm()
        self.view = View(self.llm)
        self.view.register_keybindings()


    def process_prompt(self, prompt):
        num_dots = 0
        result = {}
        for result in self.llm.ask_llm(prompt):
            self.view.printer.console.print("\r[#00ff00]" + "-", end="")
            num_dots += 1

        self.view.printer.console.print("\r[#00ff00]" + "-" * (self.view.printer.console.width - num_dots) + "[/#00ff00]")

        if result:
            self.view.printer.print_result(result)
            self.llm.gemini.add_content(role="model", text=result["model_output"])
            embedded_json_dicts = JsonExtractor().extract(result["model_output"])
            print(embedded_json_dicts)


    def run_once(self, prompt):
        result = {}
        for result in self.llm.ask_llm(prompt):
            pass
        self.view.printer.print_result(result)


    def run(self):
        self.view.printer.console.print(Markdown(help_str))

        h_llm = DefaultHandler(self.llm, self.view)
        h_url_files = FileHandler(self.llm, self.view, filehandling.UrlFileLoader(), h_llm)
        h_local_files = FileHandler(self.llm, self.view, filehandling.LocalFileLoader(), h_url_files)
        h_youtube_url = YoutubeUrlHandler(self.llm, self.view, h_local_files)
        h_empty = EmptyPromptHandler(h_youtube_url)
        h_exit = ExitHandler(h_empty)

        while True:
            try:
                prompt = self.view.get_user_input()

                continuation = h_exit.handle(prompt)
                if continuation == Continuation.BREAK:
                    break
                elif continuation == Continuation.CONTINUE:
                    continue
                elif continuation == Continuation.UNHANDLED:
                    raise ValueError(f"Prompt was not handled by anyone: {prompt}")

            except (KeyboardInterrupt):
                continue

            except (EOFError):
                break


class JsonExtractor:
    def __init__(self) -> None:
        pass

    def extract(self, text):
        json_strings = re.findall(r"(?<=```json).*?(?=```)", text, flags=re.MULTILINE| re.DOTALL)
        result = []
        for json_string in json_strings:
            tmp_result = []
            try:
                tmp_result = json.loads(json_string)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error: Could not decode json_string: {json_string}\n", e)
            if tmp_result:
                result += tmp_result

                return result

def main(argv):
    controller = ReplController()
    if len(argv) == 1:
        controller.run()
    else:
        _, *prompt = argv
        prompt = " ".join(prompt)
        controller.run_once(prompt)


if __name__ == "__main__":
    main(sys.argv)
