import re


_MD_V2_SPECIAL = r"_*[]()~`>#+-=|{}.!\\"


def escape_md_v2(text: str) -> str:
    if not text:
        return ""

    pattern = re.compile(r"([\\_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])")
    return pattern.sub(r"\\\\\1", text)
