# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types

class GeminiSearch():
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash"
        self.contents = []
        self.tools = [
            types.Tool(googleSearch=types.GoogleSearch()),
        ]
        self.generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            tools=self.tools,
            response_mime_type="text/plain",
        )


    def add_content(self, role, text):
        self.contents += [types.Content(
            role=role,
            parts=[
                types.Part.from_text(text=text),
            ],
        )]

    
    def clear_contents(self):
        self.contents = []


    def generate(self, user_prompt):
        self.add_content(role="user", text=user_prompt)
        
        tmp_result = ""
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=self.contents,
            config=self.generate_content_config,
        ):  
            tmp_result += chunk.text if chunk.text else ""
            yield chunk
        
        self.add_content(role="model", text=tmp_result)


# def generate(user_prompt):
#     client = genai.Client(
#         api_key=os.environ.get("GEMINI_API_KEY"),
#     )

#     model = "gemini-2.5-flash"
#     contents = [
#         types.Content(
#             role="user",
#             parts=[
#                 types.Part.from_text(text=user_prompt),
#             ],
#         ),
#     ]
#     tools = [
#         types.Tool(googleSearch=types.GoogleSearch(
#         )),
#     ]
#     generate_content_config = types.GenerateContentConfig(
#         thinking_config = types.ThinkingConfig(
#             thinking_budget=0,
#         ),
#         tools=tools,
#         response_mime_type="text/plain",
#     )

#     for chunk in client.models.generate_content_stream(
#         model=model,
#         contents=contents,
#         config=generate_content_config,
#     ):
#         yield chunk
    

if __name__ == "__main__":
    llm = GeminiSearch()
    for chunk in llm.generate("hi"):
        print(chunk.text)
    
