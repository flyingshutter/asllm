from google.genai import types

class GeminiModel:
    def __init__(self) -> None:
        self.thinking_budget = None
        self.name = None
        self.short_name = None

    def make_config(self, system_instruction, tool_list):
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=self.thinking_budget),
            tools=tool_list,
            system_instruction=system_instruction,
            response_mime_type="text/plain",
        )
        return config

class GEMINI_2_5_PRO(GeminiModel):
       def __init__(self) -> None:
            self.thinking_budget = 128 
            self.name = "gemini-2.5-pro"
            self.short_name = "pro"

class GEMINI_2_5_FLASH(GeminiModel):
       def __init__(self) -> None:
            self.thinking_budget = 0 
            self.name = "gemini-2.5-flash"
            self.short_name = "flash"

class GEMINI_2_5_FLASH_LITE(GeminiModel):
       def __init__(self) -> None:
            self.thinking_budget = 0 
            self.name = "gemini-2.5-flash-lite"
            self.short_name = "lite"
