import mimetypes
from typing import Protocol, Optional
import requests
import re
import os, sys

class FileLoader(Protocol):
    def load(self, file_name) -> bytes:
        ...

    def get_mimetype(self, file_name) -> (str | None):
        ...

    def validate(self, prompt) -> str:
        ...



class LocalFileLoader:
    def load(self, file_name):
        with open(file_name, "rb") as f:
            bin_data = f.read()
        return bin_data

    def get_mimetype(self, file_name):
        mimetype = mimetypes.guess_type(file_name)
        return mimetype[0]

    def validate(self, prompt) -> str:
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
                win_path = subprocess.run(f"cygpath -w {self.filepath.strip()}", capture_output=True, text=True).stdout[:-1]

                if os.path.isfile(win_path):
                    #self.console.print("win file detected", end=" | ")
                    file_name = prompt.strip()
                    return win_path
            except:
                pass

        return ""


class UrlFileLoader:
    def __init__(self) -> None:
        self.headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0"}

    def load(self, file_name):
        response = requests.get(file_name, allow_redirects=True, timeout=5, headers=self.headers) 
        return response.content

    def get_mimetype(self, file_name):
        response = requests.head(file_name, allow_redirects=True, timeout=5, headers=self.headers)
        content_type = response.headers.get('Content-Type')
        return content_type

    def validate(self, prompt) -> str:
        pat = re.compile(r"^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/%\w\.-]*)*\/?$")
        if re.fullmatch(pat, prompt):
            return prompt
        return ""


class YoutubeValidator:
    @staticmethod
    def _match(prompt) -> Optional[re.Match]:
        match = re.search(r"https://www.youtube.com/watch\?v=.{11}", prompt)
        return match

    @staticmethod
    def validate(prompt):
        return True if YoutubeValidator._match(prompt) else False

    @staticmethod
    def get_url(prompt):
        if match := YoutubeValidator._match(prompt):
            return match.string


class FileHandler:
    def __init__(self, prompt, allowed_mimetypes) -> None:
        self.prompt = prompt
        self.allowed_mimetypes = allowed_mimetypes
        # self.file_loaders = (LocalFileLoader, )
        self.file_loaders = (LocalFileLoader, UrlFileLoader)

    def handle(self):
        for fl in self.file_loaders:
            loader = fl()
            if file_name := loader.validate(self.prompt):
                mimetype = loader.get_mimetype(file_name)
                if mimetype in self.allowed_mimetypes:
                    return {"bin_data": loader.load(file_name), "mimetype": mimetype}
                return {"rejected_mime_type":True, "mimetype": mimetype}
        return {}

def main():
    allowed_mimetypes = (
        'text/',
        'application/pdf',
        "image/png", "image/jpeg", "image/webp", "image/heic", "image/heif",
        "video/mp4", "video/mpeg", "video/mov", "video/avi", "video/x-flv", "video/mpg", "video/webm", "video/wmv", "video/3gpp",
        "audio/wav", "audio/mp3", "audio/aiff", "audio/aac", "audio/ogg", "audio/flac", "audio/mpeg",
    )
    # prompt = "/home/sca04245/as/Projekte/2025-07-22_LLM/examples/mp3.mp3"
    prompt = "https://static1.chronodrive.com/img/PM/Z/0/31/0Z_186231.jpg"
    file_data = FileHandler(prompt, allowed_mimetypes).handle()
    a=0

if __name__ == "__main__":
    main()
