import json
import urllib.parse
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

from src.services.ai_client import get_openai_client, get_openai_model

YOUTUBE_HOSTS = ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com")
YOUTU_BE_HOSTS = ("youtu.be", "www.youtu.be")


def is_youtube_url(url: str) -> bool:
    hostname = (urllib.parse.urlparse(url).hostname or "").lower()
    return hostname in YOUTUBE_HOSTS or hostname in YOUTU_BE_HOSTS


def get_youtube_video_id(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()
    video_id = None

    if hostname in YOUTU_BE_HOSTS:
        video_id = parsed.path.lstrip("/").split("/")[0]
    elif hostname in YOUTUBE_HOSTS:
        if parsed.path == "/watch":
            video_id = urllib.parse.parse_qs(parsed.query).get("v", [None])[0]
        else:
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2 and parts[0] in ("shorts", "embed", "live", "v"):
                video_id = parts[1]

    if not video_id:
        raise ValueError("Invalid YouTube URL: could not find a video ID.")
    return video_id


def get_video_description(url: str) -> str:
    """Fetches the YouTube video description using yt-dlp."""
    ydl_opts = {'quiet': True, 'skip_download': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('description') or ''
    except Exception:
        return ""

EXTRACTION_PROMPT = """
You are an expert culinary assistant analyzing text from a YouTube cooking video ({source}).

CRITICAL RULES:
1. ONLY EXTRACT WHAT IS THERE: Extract ingredients and instructions only if they actually appear in the text.
   Never invent, guess or deduce ingredients or steps that are not present. If a part is missing, return an empty list for it.
2. LANGUAGE: Output in the EXACT SAME LANGUAGE as the source text. Do not translate.
3. AMOUNTS: If exact amounts are missing, write ingredients as spoken/written.
4. MISSING DATA: If prep_time, cook_time (in minutes) or servings are not mentioned, return null.
5. NOT A RECIPE: If the text contains neither ingredients nor instructions, return empty lists and a null title.
{known_section}
Return ONLY a valid JSON object with this structure:
{{
    "title": "A short, descriptive title" or null,
    "ingredients": ["item 1", "item 2"],
    "instructions": ["step 1", "step 2"],
    "prep_time": null,
    "cook_time": null,
    "servings": null
}}
"""

KNOWN_SECTION = """
CONTEXT: The video description already provided this partial recipe:
{known_json}
Use the transcript to complete what is missing (especially the instructions). Keep the steps consistent
with the ingredients listed above.
"""

TRANSCRIPT_LANGUAGES = ["he", "iw", "en", "en-US", "en-GB"]


def _clean_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if item is not None and str(item).strip()]


def _attempt_ai_extraction(
    text_content: str, client: OpenAI, model: str, source: str, known: dict | None = None
) -> dict:
    """Runs the extraction prompt and returns a normalized dict (lists always present, may be empty)."""
    empty = {"title": None, "ingredients": [], "instructions": [],
             "prep_time": None, "cook_time": None, "servings": None}
    if not text_content or not text_content.strip():
        return empty

    known_section = ""
    if known:
        known_section = KNOWN_SECTION.format(known_json=json.dumps(known, ensure_ascii=False, indent=2))

    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT.format(source=source, known_section=known_section)},
            {"role": "user", "content": f"Here is the source text:\n\n{text_content}"},
        ],
    )
    data = json.loads(response.choices[0].message.content)
    if not isinstance(data, dict):
        return empty

    title = data.get("title")
    return {
        "title": title.strip() if isinstance(title, str) and title.strip() else None,
        "ingredients": _clean_list(data.get("ingredients")),
        "instructions": _clean_list(data.get("instructions")),
        "prep_time": data.get("prep_time"),
        "cook_time": data.get("cook_time"),
        "servings": data.get("servings"),
    }


def get_video_transcript(video_id: str) -> str:
    """Fetches the spoken transcript of the video. Raises ValueError if unavailable."""
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=TRANSCRIPT_LANGUAGES)
        return " ".join(snippet.text for snippet in fetched)
    except Exception as e:
        raise ValueError(f"Could not retrieve the video transcript. Details: {e}") from e


def _merge(description_data: dict, transcript_data: dict) -> dict:
    """Description wins wherever it has data (written amounts are more accurate);
    the transcript fills in whatever the description is missing."""
    merged = {}
    for key, desc_value in description_data.items():
        transcript_value = transcript_data.get(key)
        if isinstance(desc_value, list):
            merged[key] = desc_value or transcript_value or []
        else:
            merged[key] = desc_value if desc_value is not None else transcript_value
    return merged


def extract_recipe_from_youtube(url: str) -> dict:
    """
    1. Extract from the description. If it has both ingredients and instructions, use it
       and skip the transcript entirely.
    2. Otherwise (no recipe, or e.g. ingredients without instructions), read the transcript
       and use it to fill in only the missing parts.
    """
    video_id = get_youtube_video_id(url)
    client = get_openai_client()
    target_model = get_openai_model("OPENAI_YOUTUBE_MODEL", default="gpt-4o")

    description = get_video_description(url)
    from_description = _attempt_ai_extraction(description, client, target_model, source="the video description")

    if from_description["ingredients"] and from_description["instructions"]:
        return from_description

    partial = from_description["ingredients"] or from_description["instructions"]

    try:
        transcript = get_video_transcript(video_id)
    except ValueError as e:
        if partial:
            missing = "instructions" if from_description["ingredients"] else "ingredients"
            raise ValueError(
                f"The description has a partial recipe but no {missing}, and the transcript is unavailable. {e}"
            ) from e
        raise ValueError(f"No recipe found in the description, and the transcript is unavailable. {e}") from e

    from_transcript = _attempt_ai_extraction(
        transcript, client, target_model, source="the spoken transcript",
        known=from_description if partial else None,
    )
    result = _merge(from_description, from_transcript)

    if not result["ingredients"] or not result["instructions"]:
        raise ValueError("Could not find a complete recipe in the video description or transcript.")

    return result
