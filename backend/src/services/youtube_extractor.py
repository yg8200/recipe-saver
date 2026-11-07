import json
import os
import urllib.parse
from dotenv import load_dotenv
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi

# Load environment variables from .env
load_dotenv()


def get_openai_client() -> OpenAI:
    """Initializes and returns the OpenAI client using the API key from the environment."""
    api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("AI_BASE_URL")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment or .env file.")
    return OpenAI(api_key=api_key, base_url=base_url)


def get_youtube_video_id(url: str) -> str:
    """Extracts the YouTube video ID from standard, short, and Shorts URLs."""
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname == "youtu.be":
        return parsed.path[1:]
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            return urllib.parse.parse_qs(parsed.query)["v"][0]
        elif parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]
    raise ValueError("Invalid or unsupported YouTube URL")


def extract_recipe_from_youtube(url: str) -> dict:
    # 1. Extract the video ID from the URL
    video_id = get_youtube_video_id(url)

    # 2. Fetch the transcript (prioritize Hebrew, then English)
    # 2. Fetch the transcript (prioritize Hebrew, then English)
    # 2. Fetch the transcript (prioritize Hebrew 'he', legacy Hebrew 'iw', then English variations)
    try:
        requested_languages = ["he", "iw", "en", "en-US", "en-GB"]
        
        ytt_api = YouTubeTranscriptApi()
        if hasattr(ytt_api, "fetch"):
            # youtube-transcript-api >= 1.0.0
            fetched_transcript = ytt_api.fetch(video_id, languages=requested_languages)
            spoken_text = " ".join([snippet.text for snippet in fetched_transcript])
        else:
            # Fallback for youtube-transcript-api < 1.0.0
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=requested_languages)
            spoken_text = " ".join([entry["text"] for entry in transcript_data])
            
    except Exception as e:
        raise ValueError(f"Could not retrieve transcript for this video. Details: {str(e)}")

    # 3. Initialize the OpenAI client
    client = get_openai_client()

    system_prompt = """
    You are an expert culinary assistant. You will be provided with the audio transcript of a cooking video.
    Extract the recipe details exactly as the chef explains them.

    CRITICAL RULES:
    1. Deduce the correct ingredients, amounts, and step-by-step instructions from the transcript.
    2. If exact amounts are not specified (e.g., "some olive oil"), write it as spoken (e.g., "מעט שמן זית").
    3. Keep all extracted text in Hebrew (if the transcript is in Hebrew) or the original language.
    4. If prep_time, cook_time, or servings are not mentioned, return null.

    Return ONLY a valid JSON object matching this structure:
    {
        "title": "A short, descriptive title based on the video",
        "ingredients": ["1 כוס קמח", "2 ביצים"],
        "instructions": ["לערבב את הקמח והביצים", "לאפות ב-180 מעלות"],
        "prep_time": null,
        "cook_time": null,
        "servings": null
    }
    """

    target_model = os.getenv("AI_MODEL_NAME", "gpt-4o")

    response = client.chat.completions.create(
        model=target_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the video transcript:\n\n{spoken_text}"},
        ],
    )

    return json.loads(response.choices[0].message.content)