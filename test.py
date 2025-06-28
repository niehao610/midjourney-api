import app.handler as handler
from lib.prompt import BANNED_PROMPT
from exceptions import BannedPromptError
from app.routers import _download_and_split_file

def check_banned(prompt: str):
    words = set(w.lower() for w in prompt.split())

    v = words & BANNED_PROMPT
    print(v)
    if len(v) != 0:
        raise BannedPromptError(f"banned prompt: {prompt}")


if __name__ == "__main__":
    result_url = "https://cdn.discordapp.com/attachments/1384158875657175166/1388174559273816084/forrynie.1981_5427551529Editorial_fashion_photography_a_chic_wo_db3cd6ed-9ec1-4090-8242-aec28672c2ed.png?ex=686005cd&is=685eb44d&hm=2fde189dc50f1ac6105bd263918e1d96ec897259514d921571a5b4321ffe54e3"
    result_local_path = _download_and_split_file(result_url, "./downloads")
    print(result_local_path)