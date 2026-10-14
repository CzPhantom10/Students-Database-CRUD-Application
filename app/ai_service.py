import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def build_system_prompt(records: List[Dict[str, Any]]) -> str:
    return (
        "You are an assistant for a student management system. "
        "Answer the user's question directly and concisely based strictly on the student database context provided below. "
        "Do not invent facts. If the information cannot be deduced from the data, say so clearly.\n\n"
        f"STUDENT DATABASE RECORDS ({len(records)} records available):\n"
        f"{json.dumps(records, indent=2)}"
    )


def query_g4f(question: str, records: List[Dict[str, Any]], model: str = "auto") -> Dict[str, Any]:
    try:
        from g4f.client import Client
        client = Client()
        system_prompt = build_system_prompt(records)
        target_model = model if model and model != "auto" else "auto"

        response = client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            web_search=False
        )
        content = response.choices[0].message.content or "No response returned from model."
        return {
            "answer": content.strip(),
            "status": "success",
            "provider": "g4f",
            "model_used": target_model,
            "context_records_count": len(records)
        }
    except Exception as e:
        return {
            "answer": f"g4f query could not reach provider: {str(e)}",
            "status": "error",
            "provider": "g4f",
            "model_used": model or "auto",
            "context_records_count": len(records)
        }


def query_ollama(question: str, records: List[Dict[str, Any]], model: str = "llama3.2:1b") -> Dict[str, Any]:
    system_prompt = build_system_prompt(records)
    target_model = model if model and model != "auto" else "llama3.2:1b"

    payload = {
        "model": target_model,
        "prompt": f"{system_prompt}\n\nUser Question: {question}\nAnswer:",
        "stream": False
    }

    url = f"{OLLAMA_HOST}/api/generate"
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "answer": data.get("response", "").strip(),
                "status": "success",
                "provider": "ollama",
                "model_used": target_model,
                "context_records_count": len(records)
            }
    except urllib.error.URLError:
        return {
            "answer": (
                f"Ollama server is not currently reachable at {OLLAMA_HOST}. "
                f"To use local Ollama, start it locally ('ollama run {target_model}' or 'ollama serve'). "
                f"Alternatively, set provider='g4f' in the request to query free cloud models without Ollama! "
                f"The backend successfully retrieved {len(records)} student records for context."
            ),
            "status": "ollama_offline",
            "provider": "ollama",
            "model_used": target_model,
            "context_records_count": len(records)
        }
    except Exception as e:
        return {
            "answer": f"AI query encountered an error: {str(e)}",
            "status": "error",
            "provider": "ollama",
            "model_used": target_model,
            "context_records_count": len(records)
        }


def query_ai(
    question: str,
    records: List[Dict[str, Any]],
    provider: str = "g4f",
    model: str = "auto"
) -> Dict[str, Any]:
    prov = (provider or "g4f").lower().strip()

    if prov == "ollama":
        return query_ollama(question, records, model=model)
    elif prov == "g4f":
        return query_g4f(question, records, model=model)
    else:
        res = query_g4f(question, records, model=model)
        if res.get("status") == "success":
            return res
        return query_ollama(question, records, model=model)
