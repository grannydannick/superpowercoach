#!/usr/bin/env python3
"""
RAG workflow for Superpower Coach email generation.

Usage:
  python rag_workflow.py --input /path/to/input.json
  python rag_workflow.py --input input.json --format json --rag-output rag.json
  python rag_workflow.py --input input.json --format prompt --output combined_prompt.txt
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class ProtocolChunk:
    title: str
    protocol_name: str
    body: str
    primary_recommendation: str
    secondary_recommendations: str
    safety_considerations: str
    evidence_sources: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def normalize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    return [t for t in cleaned.split() if t]


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa = set(a)
    sb = set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def extract_code_blocks(text: str) -> List[str]:
    return re.findall(r"```(?:\w+)?\n(.*?)```", text, flags=re.S)


def split_protocol_blocks(block: str) -> List[str]:
    lines = block.splitlines()
    chunks: List[List[str]] = []
    current: List[str] = []
    for line in lines:
        if line.strip().startswith("## "):
            if current:
                chunks.append(current)
            current = [line]
        else:
            if current:
                current.append(line)
    if current:
        chunks.append(current)
    return ["\n".join(c).strip() for c in chunks]


def extract_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^###\s+{re.escape(heading)}\s*$",
        flags=re.M,
    )
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^###\s+.+\s*$", text[start:], flags=re.M)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def parse_protocol_chunks(protocols_text: str) -> List[ProtocolChunk]:
    chunks: List[ProtocolChunk] = []
    for block in extract_code_blocks(protocols_text):
        for chunk_text in split_protocol_blocks(block):
            lines = chunk_text.splitlines()
            title_line = lines[0].strip()
            title = title_line.replace("##", "", 1).strip()
            protocol_name = ""
            for line in lines:
                if line.strip().startswith("**Protocol:**"):
                    protocol_name = line.replace("**Protocol:**", "").strip()
                    break
            primary = extract_section(chunk_text, "Primary Recommendation")
            secondary = extract_section(chunk_text, "Secondary Recommendations")
            safety = extract_section(chunk_text, "Safety Considerations")
            evidence = extract_section(chunk_text, "Evidence Sources")
            chunks.append(
                ProtocolChunk(
                    title=title,
                    protocol_name=protocol_name,
                    body=chunk_text.strip(),
                    primary_recommendation=primary,
                    secondary_recommendations=secondary,
                    safety_considerations=safety,
                    evidence_sources=evidence,
                )
            )
    return chunks


def best_match_protocol(
    query: str,
    protocol_chunks: List[ProtocolChunk],
) -> Optional[ProtocolChunk]:
    query_tokens = normalize(query)
    best: Tuple[float, Optional[ProtocolChunk]] = (0.0, None)
    for chunk in protocol_chunks:
        score = max(
            jaccard(query_tokens, normalize(chunk.title)),
            jaccard(query_tokens, normalize(chunk.protocol_name)),
        )
        if score > best[0]:
            best = (score, chunk)
    return best[1]


def build_rag_protocols(
    selected_protocols: List[Dict[str, Any]],
    protocol_chunks: List[ProtocolChunk],
) -> List[Dict[str, Any]]:
    rag_protocols: List[Dict[str, Any]] = []
    for item in selected_protocols:
        theme = str(item.get("theme", "")).strip()
        protocol_name = str(item.get("protocol_name", "")).strip()
        query = " ".join([theme, protocol_name]).strip()
        matched = best_match_protocol(query, protocol_chunks)
        rag_protocols.append(
            {
                "rank": item.get("rank"),
                "theme": theme,
                "protocol_name": protocol_name,
                "evidence_source": item.get("evidence_source"),
                "matched_protocol_title": matched.title if matched else "",
                "protocol_details": {
                    "primary_recommendation": matched.primary_recommendation
                    if matched
                    else "",
                    "secondary_recommendations": matched.secondary_recommendations
                    if matched
                    else "",
                    "safety_considerations": matched.safety_considerations
                    if matched
                    else "",
                    "evidence_sources": matched.evidence_sources if matched else "",
                    "full_protocol_text": matched.body if matched else "",
                },
            }
        )
    return rag_protocols


def build_prompt_input(
    input_data: Dict[str, Any],
    rag_protocols: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "B": input_data.get("B") or input_data.get("biomarker_analysis"),
        "P": input_data.get("P") or input_data.get("preference_analysis"),
        "C": input_data.get("C") or input_data.get("patient_context"),
        "PRO": input_data.get("PRO") or input_data.get("selected_protocols"),
        "PD": rag_protocols,
    }


def build_combined_prompt(prompt_text: str, prompt_input: Dict[str, Any]) -> str:
    payload = json.dumps(prompt_input, indent=2, ensure_ascii=True)
    return f"{prompt_text.rstrip()}\n\n<input>\n{payload}\n</input>\n"


def strip_code_fences(text: str) -> str:
    fenced = re.findall(r"```(?:json)?\n(.*?)```", text, flags=re.S)
    if fenced:
        return fenced[0].strip()
    return text.strip()


def call_openai_chat(
    api_base: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
) -> str:
    url = api_base.rstrip("/") + "/v1/chat/completions"
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def generate_synthetic_input(
    free_text: str,
    protocol_chunks: List[ProtocolChunk],
    api_base: str,
    api_key: str,
    model: str,
) -> Dict[str, Any]:
    allowed = [
        {"theme": chunk.title, "protocol_name": chunk.protocol_name}
        for chunk in protocol_chunks
        if chunk.protocol_name
    ]
    system_prompt = (
        "You generate synthetic member input JSON for Superpower Coach. "
        "Return ONLY valid JSON with keys: B, P, C, PRO. "
        "PRO must include exactly 3 items with fields: rank (1-3), theme, "
        "protocol_name, evidence_source. "
        "Choose protocol_name and theme ONLY from the provided allowed list. "
        "If data is missing, use brief conceptual placeholders instead of numbers. "
        "Do not include any extra keys or commentary."
    )
    user_prompt = json.dumps(
        {
            "free_text": free_text,
            "allowed_protocols": allowed,
            "required_schema": {
                "B": {
                    "top_themes": [
                        {"theme": "string", "pattern_strength": "0-5"}
                    ],
                    "abnormal_values": [
                        {"marker": "string", "value": "string", "range": "string"}
                    ],
                    "pattern_classification": "Significant/Isolated",
                    "clinical_severity": "string",
                },
                "P": {
                    "preference_themes": ["string"],
                    "symptoms": [{"symptom": "string", "severity": "string"}],
                    "goals": ["string"],
                },
                "C": {
                    "demographics": {"age": "string", "sex": "string"},
                    "medical_history": ["string"],
                    "medications": ["string"],
                    "supplements": ["string"],
                    "dietary_restrictions": ["string"],
                    "allergies": ["string"],
                    "lifestyle": {"activity": "string", "sleep": "string", "stress": "string"},
                },
                "PRO": [
                    {
                        "rank": 1,
                        "theme": "string",
                        "protocol_name": "string",
                        "evidence_source": "Biomarker/Preference/Merged/Foundations",
                    }
                ],
            },
        },
        indent=2,
        ensure_ascii=True,
    )
    content = call_openai_chat(
        api_base=api_base,
        api_key=api_key,
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    json_text = strip_code_fences(content)
    return json.loads(json_text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RAG workflow for Superpower Coach")
    parser.add_argument(
        "--input",
        help="Path to input JSON (optional if --free-text is provided)",
    )
    parser.add_argument(
        "--free-text",
        help="Free text to generate synthetic input JSON with LLM",
    )
    parser.add_argument(
        "--protocols",
        default="protocols.txt",
        help="Path to protocols.txt",
    )
    parser.add_argument(
        "--prompt",
        default="prompt.txt",
        help="Path to prompt.txt",
    )
    parser.add_argument(
        "--format",
        default="prompt",
        choices=["prompt", "json"],
        help="Output format: full prompt or JSON only",
    )
    parser.add_argument("--output", help="Path to write output")
    parser.add_argument(
        "--rag-output",
        help="Optional path to write RAG protocol JSON",
    )
    parser.add_argument(
        "--synthetic-output",
        help="Optional path to write synthetic input JSON",
    )
    parser.add_argument(
        "--llm-model",
        default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        help="LLM model name (default from OPENAI_MODEL)",
    )
    parser.add_argument(
        "--llm-api-base",
        default=os.getenv("OPENAI_API_BASE", "https://api.openai.com"),
        help="LLM API base URL (default from OPENAI_API_BASE)",
    )
    parser.add_argument(
        "--llm-api-key",
        default=os.getenv("OPENAI_API_KEY", ""),
        help="LLM API key (default from OPENAI_API_KEY)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocols_path = Path(args.protocols)
    prompt_path = Path(args.prompt)

    load_dotenv(Path(".env"))

    protocols_text = read_text(protocols_path)
    prompt_text = read_text(prompt_path)

    protocol_chunks = parse_protocol_chunks(protocols_text)
    if args.free_text:
        if not args.llm_api_key:
            raise ValueError(
                "LLM API key missing. Set OPENAI_API_KEY or pass --llm-api-key."
            )
        input_data = generate_synthetic_input(
            free_text=args.free_text,
            protocol_chunks=protocol_chunks,
            api_base=args.llm_api_base,
            api_key=args.llm_api_key,
            model=args.llm_model,
        )
        if args.synthetic_output:
            Path(args.synthetic_output).write_text(
                json.dumps(input_data, indent=2, ensure_ascii=True),
                encoding="utf-8",
            )
    else:
        if not args.input:
            raise ValueError("Provide --input or --free-text.")
        input_path = Path(args.input)
        input_data = json.loads(read_text(input_path))

    selected_protocols = input_data.get("PRO") or input_data.get("selected_protocols")
    if not isinstance(selected_protocols, list):
        raise ValueError("Input JSON must include PRO or selected_protocols as a list.")

    rag_protocols = build_rag_protocols(selected_protocols, protocol_chunks)

    if args.rag_output:
        Path(args.rag_output).write_text(
            json.dumps(rag_protocols, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    prompt_input = build_prompt_input(input_data, rag_protocols)
    if args.format == "json":
        output_text = json.dumps(prompt_input, indent=2, ensure_ascii=True)
    else:
        output_text = build_combined_prompt(prompt_text, prompt_input)

    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
