import os
import json
import re
from typing import Optional, Dict, Any, Tuple


def _strip_code_fences(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```$", "", t)
    return t.strip()


def _try_json_load(text: str) -> Optional[dict]:
    """
    Try parse JSON robustly:
    - strip ```json fences
    - fix smart quotes
    - add missing closing brace if clearly truncated
    - fallback: find first {...} block
    """
    if not text:
        return None

    t = _strip_code_fences(text)

    # Replace smart quotes if any
    t = t.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'").strip()

    # Try direct
    try:
        return json.loads(t)
    except Exception:
        pass

    # Try extract first JSON object
    m = re.search(r"\{.*", t, flags=re.DOTALL)
    if m:
        candidate = m.group(0).strip()
        # If looks like truncated JSON object, try closing it
        if candidate.startswith("{") and candidate.count("{") > candidate.count("}"):
            candidate = candidate + "}"
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Try find a balanced {...}
    m2 = re.search(r"\{.*\}", t, flags=re.DOTALL)
    if m2:
        try:
            return json.loads(m2.group(0))
        except Exception:
            return None

    return None


def _load_genai() -> Tuple[Optional[object], Optional[str]]:
    try:
        import google.generativeai as genai
    except Exception as e:
        return None, f"Gemini library missing/incompatible: {str(e)[:160]}"

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None, "Missing GEMINI_API_KEY. Put it in .env and restart the server."

    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        return None, f"Failed to configure Gemini client: {str(e)[:160]}"

    return genai, None


def _pick_model_name() -> list:
    """
    Try a list of candidates in case the provided name changes.
    """
    env_model = (os.getenv("GEMINI_MODEL") or "").strip()
    candidates = []
    if env_model:
        candidates.append(env_model)
    # safe fallbacks
    candidates += ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-flash-latest"]

    # Also try with "models/" prefix if needed
    extra = []
    for m in candidates:
        if not m.startswith("models/"):
            extra.append("models/" + m)
    return list(dict.fromkeys(candidates + extra))  # unique, keep order


def _generate_json(model, prompt: str, image_bytes: bytes, mime_type: str) -> str:
    # Force JSON output if supported
    generation_config = {
        "temperature": 0.2,
        "max_output_tokens": 300,
        "response_mime_type": "application/json",
    }
    resp = model.generate_content(
        [prompt, {"mime_type": mime_type, "data": image_bytes}],
        generation_config=generation_config,
    )
    return (getattr(resp, "text", "") or "").strip()


def analyze_food_image(image_path: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
    try:
        genai, err = _load_genai()
        if err:
            return {"success": False, "error": err}

        if not os.path.exists(image_path):
            return {"success": False, "error": "Image file not found"}

        file_ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        if file_ext not in mime_map:
            return {"success": False, "error": "Invalid image format. Use jpg/jpeg/png/gif/webp."}

        mime_type = mime_map[file_ext]
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        prompt = (
            "You are a food identification assistant.\n"
            "Return ONLY valid JSON with EXACTLY these keys:\n"
            '{ "name": "<Dish Name>", "description": "<1-2 English sentences>" }\n'
            "Rules:\n"
            "- name: 2–6 words, Title Case.\n"
            "- description: concise, accurate to the image.\n"
            "- Output must be valid JSON (double quotes, no trailing commas).\n"
            "No markdown, no extra text."
        )

        # Try models + retry if output not valid
        last_text = ""
        for model_name in _pick_model_name():
            try:
                model = genai.GenerativeModel(model_name)
                # Attempt 1
                last_text = _generate_json(model, prompt, image_bytes, mime_type)
                data = _try_json_load(last_text)

                # If missing keys or invalid -> retry once with stronger constraint
                if not data or "name" not in data or "description" not in data:
                    retry_prompt = (
                        "Your previous output was invalid or incomplete.\n"
                        "Return ONLY valid JSON with keys: name, description.\n"
                        "No markdown. No extra text.\n"
                        '{ "name": "…", "description": "…" }'
                    )
                    last_text = _generate_json(model, retry_prompt, image_bytes, mime_type)
                    data = _try_json_load(last_text)

                if data and "name" in data and "description" in data:
                    name = str(data.get("name", "")).strip()
                    desc = str(data.get("description", "")).strip()
                    if name and desc:
                        return {"success": True, "name": name, "description": desc}

            except Exception:
                continue

        # If all failed, show a helpful snippet
        snippet = (last_text or "")[:220]
        return {"success": False, "error": f"Gemini returned invalid JSON. Snippet: {snippet}"}

    except Exception as e:
        msg = str(e)
        if "404" in msg and "models" in msg:
            return {"success": False, "error": "Model not found. Change GEMINI_MODEL in .env and restart server."}
        if "API key" in msg or "401" in msg or "unauth" in msg.lower():
            return {"success": False, "error": "Invalid or missing API key. Check GEMINI_API_KEY and restart server."}
        return {"success": False, "error": f"Error: {msg[:200]}"}