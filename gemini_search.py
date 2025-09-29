################################################################################
#               https://ai.google.dev/gemini-api/docs                          #
################################################################################
import os
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
import models


allowed_mimetypes = (
    'text/plain',
    'application/pdf',
    "image/png", "image/jpeg", "image/webp", "image/heic", "image/heif",
    "video/mp4", "video/mpeg", "video/mov", "video/avi", "video/x-flv", "video/mpg", "video/webm", "video/wmv", "video/3gpp",
    "audio/wav", "audio/mp3", "audio/aiff", "audio/aac", "audio/ogg", "audio/flac", "audio/mpeg",
)


class GeminiSearch():
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

        self._system_instruction = ""
        self.tools_state = {"url_context":True, "google_search":True}

        self.known_models = (models.GEMINI_2_5_PRO, models.GEMINI_2_5_FLASH, models.GEMINI_2_5_FLASH_LITE)
        self.model = self.known_models[1]()
        self.contents = []


    @property
    def system_instruction(self):
        return self._system_instruction

    @system_instruction.setter
    def system_instruction(self, text):
        self._system_instruction = text


    def make_tool_list(self):
        tools = []
        if self.tools_state['url_context']:
            tools += [types.Tool(url_context=types.UrlContext())]
        if self.tools_state['google_search']:
            tools += [types.Tool(google_search=types.GoogleSearch())]

        return tools


    def set_tool_state(self, tool_name, set_active):
        self.tools_state[tool_name] = set_active


    def add_content(self, role, text):
        self.contents += [types.Content(
            role=role,
            parts=[
                types.Part.from_text(text=text),
            ],
        )]


    def add_file_to_content(self, bin_data, mime_type):
        self.contents += [types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    mime_type=mime_type,
                    data=bin_data,
                ),
            ],
        )]

    def add_youtube_video_to_content(self, url):
        self.contents += [types.Content(
            role="user",
            parts = [ types.Part( file_data=types.FileData(file_uri=url) ), ]
        )]

    def clear_contents(self):
        self.contents = []


    def generate_stream(self, user_prompt):
        tool_list = self.make_tool_list()
        config = self.model.make_config(self._system_instruction, tool_list)
        self.add_content(role="user", text=user_prompt)

        try:
            for chunk in self.client.models.generate_content_stream(model=self.model.name, contents=self.contents, config=config):  
               yield chunk
        except (ClientError, ServerError) as e:
            print(e)


if __name__ == "__main__":
    llm = GeminiSearch()
    for chunk in llm.generate_stream("hi"):
        print(chunk.text)

