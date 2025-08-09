import os
from google import genai
from google.genai import types


class GeminiSearch():
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

        self.system_instruction = [types.Part.from_text(text="answer short and precise, do not explain your answer")]
        self.tools = [types.Tool(googleSearch=types.GoogleSearch())]
        self.make_config()

        self.model = "gemini-2.5-flash"
        self.contents = []


    def make_config(self):
        self.config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            tools=self.tools,
            system_instruction=self.system_instruction,
            response_mime_type="text/plain",
        )


    def update_system_instruction(self, instruction):
        self.system_instruction = [types.Part.from_text(text=instruction)]    
        self.make_config()
 

    def switch_google_search(self, state):
        if state:
            self.tools = [types.Tool(googleSearch=types.GoogleSearch())]
        else:
            self.tools = []
        self.make_config()

        
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
        
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=self.contents,
            config=self.config,
        ):  
            yield chunk
        


if __name__ == "__main__":
    llm = GeminiSearch()
    for chunk in llm.generate("hi"):
        print(chunk.text)
    
