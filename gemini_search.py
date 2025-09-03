################################################################################
#               https://ai.google.dev/gemini-api/docs                          #
################################################################################
import os, base64, mimetypes
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError


class GeminiSearch():
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

        self._system_instruction = [types.Part.from_text(text="")]
        self.tools_state = {"url_context":True, "google_search":True}

        self.model = "gemini-2.5-flash"
        self.contents = []


    @property
    def system_instruction(self):
        return self._system_instruction[0].text

    @system_instruction.setter
    def system_instruction(self, text):
        self._system_instruction = [types.Part.from_text(text=text)]


    def make_tool_list(self):
        tools = []
        if self.tools_state['url_context']:
            tools += [types.Tool(url_context=types.UrlContext())]
        if self.tools_state['google_search']:
            tools += [types.Tool(google_search=types.GoogleSearch())]

        return tools


    def make_config(self):
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            tools=self.make_tool_list(),
            system_instruction=self._system_instruction,
            response_mime_type="text/plain",
        )
        return config


    def set_tool_state(self, tool_name, set_active):
        self.tools_state[tool_name] = set_active


    def add_content(self, role, text):
        self.contents += [types.Content(
            role=role,
            parts=[
                types.Part.from_text(text=text),
            ],
        )]


    def add_file_to_content(self, file_name):
        mime_type = mimetypes.guess_type(file_name)[0]
        with open(file_name, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode('utf-8')
        with open(file_name, "rb") as f:
            bin_data = f.read()

        self.contents += [types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    mime_type=mime_type,
                    data=bin_data,
                ),
            ],
        )]


    def clear_contents(self):
        self.contents = []


    def generate(self, user_prompt):
        self.add_content(role="user", text=user_prompt)

        try:
            for chunk in self.client.models.generate_content_stream(model=self.model, contents=self.contents, config=self.make_config()):  
               yield chunk
        except (ClientError, ServerError) as e:
            print(e)


if __name__ == "__main__":
    llm = GeminiSearch()
    for chunk in llm.generate("hi"):
        print(chunk.text)

