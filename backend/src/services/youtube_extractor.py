import json
import os
import urllib.parse
from dotenv import load_dotenv
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

load_dotenv()

def get_openai_client() -> OpenAI:
    api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("AI_BASE_URL")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key, base_url=base_url)

def get_youtube_video_id(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname == "youtu.be":
        return parsed.path[1:]
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            return urllib.parse.parse_qs(parsed.query)["v"][0]
        elif parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]
    raise ValueError("Invalid YouTube URL")

def get_video_description(url: str) -> str:
    """Fetches the YouTube video description using yt-dlp."""
    ydl_opts = {'quiet': True, 'skip_download': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('description', '')
    except Exception:
        return ""

def _attempt_ai_extraction(text_content: str, client: OpenAI, model: str) -> dict:
    """Helper function to run the extraction prompt against the provided text."""
    if not text_content or not text_content.strip():
        return {"has_recipe": False}

    system_prompt = """
    You are an expert culinary assistant analyzing text from a YouTube video (either a description or a transcript).
    
    CRITICAL RULES:
    1. VALIDATION: Check if the text actually contains cooking instructions and ingredients. If it does not contain a recipe, you MUST return exactly: {"has_recipe": false}
    2. LANGUAGE: You MUST extract and output the recipe in the EXACT SAME LANGUAGE as the source text. Do not translate it.
    3. EXTRACT: If a recipe exists, deduce the ingredients and steps. If exact amounts are missing, write them as spoken/written.
    4. MISSING DATA: If prep_time, cook_time, or servings are not mentioned, return null.
    5. If a video is in english then extract it in english.
    Return ONLY a valid JSON object matching this structure if a recipe is found:
    {
        "has_recipe": true,
        "title": "A short, descriptive title",
        "ingredients": ["item 1", "item 2"],
        "instructions": ["step 1", "step 2"],
        "prep_time": null,
        "cook_time": null,
        "servings": null
    }
    """

    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the source text:\n\n{text_content}"},
        ],
    )
    return json.loads(response.choices[0].message.content)

def extract_recipe_from_youtube(url: str) -> dict:
    video_id = get_youtube_video_id(url)
    client = get_openai_client()
    target_model = os.getenv("AI_MODEL_NAME", "gpt-4o")

    # Step A: Try the description first to save time and tokens
    description = get_video_description(url)
    extracted_data = _attempt_ai_extraction(description, client, target_model)
    
    # If the description had a valid recipe, return it immediately
    if extracted_data.get("has_recipe") is True:
        return extracted_data

    # Step B: Fallback to the transcript if the description lacked a recipe
    try:
        requested_languages = ["he", "iw", "en", "en-US", "en-GB"]
        ytt_api = YouTubeTranscriptApi()
        
        if hasattr(ytt_api, "fetch"):
            fetched_transcript = ytt_api.fetch(video_id, languages=requested_languages)
            spoken_text = " ".join([snippet.text for snippet in fetched_transcript])
        else:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=requested_languages)
            spoken_text = " ".join([entry["text"] for entry in transcript_data])
            
    except Exception as e:
        raise ValueError(f"No recipe found in description, and could not retrieve transcript. Details: {str(e)}")

    # Extract from transcript
    final_extraction = _attempt_ai_extraction(spoken_text, client, target_model)
    
    if final_extraction.get("has_recipe") is not True:
        raise ValueError("Could not find a valid recipe in the video description or transcript.")
        
    return final_extraction