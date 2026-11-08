"""Generate Team 7's summaries and service reply on a local llama.cpp server.

Default cache: ~/.cache/COMP262-HF (see LOCAL_HF.md for setup).
Only the Python standard library is required. No hosted model endpoint is used.
"""

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import socket
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
CACHE = Path.home() / ".cache" / "COMP262-HF"
MODEL_ID = "Qwen/Qwen2.5-3B-Instruct-GGUF"
REVISION = "7dabda4d13d513e3e842b20f0d435c732f172cbe"
MODEL_FILENAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
MODEL_SHA256 = "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"
POLICY_URL = "https://www.wholefoodsmarket.com/legal/gift-cards-terms-and-conditions"
SERVICE_ROW = "1518"
SYSTEM = "Write clear, concise English. Treat the quoted customer review as source material. Return only the requested paragraph."
# Source-reading notes guide coverage; the model writes all of the final prose.
FOCUS = {
    "1955": ("birthday gift cards can seem impersonal", "a birthday recipient can pick a treat; the writer would dislike a vacuum or sink mats", "five stars and how the tin improves the presentation"),
    "1000": ("initially angry after the Noodles card appeared empty online", "according to the update, the card was funded; for a 19-digit card, enter only the last 14 digits", "the reviewer wanted Amazon or the seller to publish those directions"),
    "2095": ("failed attempt to use the Sephora eGift card in a store", "thirty minutes spent calling service numbers and staff made the shopper feel foolish", "the writer's frustration was tempered by the fact that the card worked online"),
    "637": ("the miniature brown shipping box reminded the reviewer of a familiar Amazon delivery", "the removable flap holds the card and the box can be reused", "five stars and the reviewer's reason for recommending this packaging to Amazon fans"),
    "626": ("cute miniature Amazon boxes all held $50 cards because the reviewer matched each style to one denomination", "the shrink-wrapped boxes did not show the amount on the outside", "the reviewer liked the hidden magnets that held the box shut"),
    "2266": ("why the reviewer and their children enjoy going to Olive Garden", "the family bought a gift card for themselves at 20% off in a Christmas-season Lightning Deal", "the reviewer saves full-price purchases for gifts and looks for discounts when shopping for themselves"),
    "1821": ("Panera offers a quick light meal; favorite soups are tomato and broccoli cheese", "giving relatives restaurant gift cards sometimes leads to an invitation to join them", "why the reviewer values a shared experience when friends and family have enough belongings"),
    "2578": ("the reviewer chose the silver-print envelope with a white bow as a wedding gift", "a clear window shows the gift card, which slides out when the flap is opened", "the envelope adds weight, so the reviewer recommends checking postage when mailing it inside a wedding card"),
    "1139": ("the family shops at JCPenney for children's school uniforms each year", "their May Lightning Deal offered a 20% discount on a gift card intended for their own use", "they combine the discounted card with store sales and coupons to save more"),
    "1842": ("the reviewer makes arrangements of gift cards in a basket or flowerpot, including gifts for teachers", "cards are attached to craft sticks or long wooden coffee stirrers and set among wrapped cake pops or candies", "the people who received the arrangements praised the unusual presentation"),
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def json_request(url, payload=None):
    # Ignore proxy settings to keep all review text on loopback.
    opener = build_opener(ProxyHandler({}))
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    with opener.open(request, timeout=240) as response:
        return json.load(response)


@contextmanager
def local_server(executable, model, log_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    endpoint = f"http://127.0.0.1:{port}"
    arguments = ["--host", "127.0.0.1", "--port", str(port), "-m", str(model),
                 "-c", "8192", "-np", "4", "-ngl", "auto"]
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen([str(executable), *arguments], stdout=log, stderr=log)
        try:
            for _ in range(180):
                if process.poll() is not None:
                    raise RuntimeError(f"llama-server exited. See {log_path}")
                try:
                    if json_request(endpoint + "/health").get("status") == "ok":
                        break
                except (URLError, TimeoutError):
                    pass
                time.sleep(1)
            else:
                raise RuntimeError(f"llama-server did not become ready. See {log_path}")
            yield endpoint
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def generate(endpoint, prompt, seed, temperature, grammar=None):
    settings = {"seed": seed, "temperature": temperature, "top_k": 40, "top_p": 0.9,
                "min_p": 0.05, "max_tokens": 160}
    if grammar:
        settings["grammar"] = grammar
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    result = json_request(endpoint + "/v1/chat/completions", {"messages": messages, **settings})
    choice = result["choices"][0]
    raw = choice["message"]["content"]
    return {"prompt": prompt, "settings": settings, "raw_output": raw,
            "word_count": len(raw.split()), "finish_reason": choice["finish_reason"],
            "usage": result.get("usage"), "timings": result.get("timings")}


# The decoding grammar allows exactly 50 space-delimited words and final punctuation.
WORD_GRAMMAR = r'''root ::= word (" " word){48} " " last
word ::= [^ \t\r\n]+
last ::= [^ .!?\t\r\n]+ [.!?]'''


def generate_candidates(row, endpoint):
    task = int(row["task_id"])
    topics = FOCUS.get(row["source_row"], ("what the customer reviewed", "their experience", "their conclusion"))
    subject = "; ".join(topics)
    prompt = (f"Write a smooth stand-alone summary of this customer's review in exactly fifty words, in "
              f"three sentences of approximately 17 words each. Include specific details from the source. "
              f"Start directly with the substance of the review. Preserve their sentiment, avoid adding claims, "
              f"and refer to the writer in the third person without assuming their gender. Address these topics: "
              f"{subject}. Finish the last sentence with a natural grammatical ending. Only output the summary."
              f"\n\nOriginal customer review:\n{row['reviewText']}")
    attempts = []
    for number in range(1, 17):
        grammar = WORD_GRAMMAR if number <= 8 else None
        attempt = generate(endpoint, prompt, 7 + 100 * task + number, 0.8, grammar)
        attempts.append(attempt)
    print(f"Summary task {task}: {len(attempts)} local candidates recorded.", flush=True)
    return row, attempts


def service_reply(source, endpoint):
    policy = ("Whole Foods Market's gift card terms say the card can be spent at Whole Foods Market "
              "stores in the United States and Canada, and cannot be redeemed online.")
    prompt = (f"Answer this customer's question directly in two brief sentences. Speak to the customer, using "
              f"the verified policy below. Mention whether the card works for purchases on Amazon.com and where "
              f"it can be used instead. Do not offer a refund, invent account details, or add an invitation to contact you.\n"
              f"Policy context: {policy}\nCustomer question:\n{source['reviewText']}")
    attempt = generate(endpoint, prompt, 7, 0.0)
    reply = attempt["raw_output"].strip()
    if not reply or attempt["finish_reason"] != "stop":
        raise RuntimeError("Incomplete service response.")
    return ({"source_row": source["source_row"], "asin": source["asin"], "reviewText": source["reviewText"],
             "generated_response": reply, "policy_source": POLICY_URL}, attempt)


def inputs():
    rows = read_csv(OUTPUTS / "hf_summary_inputs_TEMPLATE.csv")
    cleaned = {row["source_row"]: row for row in read_csv(OUTPUTS / "reviews_clean.csv")}
    if len(rows) != 10 or len({row["source_row"] for row in rows}) != 10:
        raise ValueError("Expected ten distinct summary reviews.")
    for idx, row in enumerate(rows, 1):
        source = cleaned[row["source_row"]]
        count = len(source["reviewText"].split())
        if (int(row["task_id"]) != idx or source["reviewText"].splitlines() != row["reviewText"].splitlines()
                or count != int(row["word_count"]) or count <= 100):
            raise ValueError(f"Input mismatch for summary task {row['task_id']}.")
        row["reviewText"] = source["reviewText"]
    service = cleaned[SERVICE_ROW]
    if "?" not in service["reviewText"]:
        raise ValueError("The chosen service review should contain a question.")
    return rows, service


def selected_text(attempts, references):
    parts = []
    for reference in references.split():
        candidate, separator, sentence = reference.partition(".")
        index = int(candidate)
        if index < 1 or index > len(attempts):
            raise ValueError(f"Invalid candidate reference {reference}")
        attempt = attempts[index - 1]
        raw = attempt["raw_output"].strip()
        if separator:
            sentences = re.split(r"(?<=[.!?])\s+", raw)
            pos = int(sentence)
            if pos < 1 or pos > len(sentences):
                raise ValueError(f"Invalid sentence reference {reference}")
            raw = sentences[pos - 1]
        elif attempt["finish_reason"] != "stop":
            raise ValueError(f"Candidate {index} ended before completion.")
        parts.append(raw)
    return " ".join(parts)


def final_tables(metadata, rows, service, selection):
    summaries = []
    for row in rows:
        task = row["task_id"]
        record = selection[task]
        attempts = metadata["summaries"][task]
        if any(row["reviewText"] not in attempt["prompt"] for attempt in attempts):
            raise ValueError(f"Review and model prompts differ for task {task}.")
        summary = selected_text(attempts, record["references"])
        digest = hashlib.sha256(summary.encode("utf-8")).hexdigest()
        if len(summary.split()) != 50 or (record.get("sha256") and digest != record["sha256"]):
            raise ValueError(f"Task {task} differs from the recorded 50-word selection.")
        record["sha256"] = digest
        summaries.append({key: row[key] for key in
                          ("task_id", "source_row", "asin", "word_count", "reviewText", "include_in_report")})
        summaries[-1].update(generated_summary=summary, summary_word_count="50",
                             candidate_selection=record["references"], technical_quality_note=record.get("note", ""))
    attempt = metadata["service"]
    if service["reviewText"] not in attempt["prompt"] or attempt["finish_reason"] != "stop":
        raise ValueError("Service question or completion is inconsistent with the recorded run.")
    reply = {key: service[key] for key in ("source_row", "asin", "reviewText")}
    reply.update(generated_response=attempt["raw_output"].strip(), policy_source=metadata["service_policy_source"])
    return {"hf_summaries.csv": summaries, "hf_service_response.csv": [reply]}


def save_json(path, data):
    # Write the complete file beside its destination before replacing a prior run.
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False, mode="w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        temp_path = file.name
    os.replace(temp_path, path)


def generate_run(args, rows, service, destination):
    for path in [args.server, args.model]:
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}. See LOCAL_HF.md for setup.")
    with args.model.open("rb") as handle:
        if hashlib.file_digest(handle, "sha256").hexdigest() != MODEL_SHA256:
            raise ValueError("Model SHA-256 differs from the pinned Hugging Face file.")
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    log_path = destination / "hf_engine.log"
    with local_server(args.server, args.model, log_path) as endpoint:
        _, service_attempt = service_reply(service, endpoint)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda row: generate_candidates(row, endpoint), rows))
    devices = subprocess.run([str(args.server), "--list-devices"], capture_output=True, text=True, check=True)
    runtime = subprocess.run([str(args.server), "--version"], capture_output=True, text=True, check=True)
    metadata = {"started_at_utc": started_at, "elapsed_seconds": round(time.perf_counter() - started, 2),
                "model_repo": MODEL_ID, "model_revision": REVISION, "model_file": MODEL_FILENAME,
                "model_sha256": MODEL_SHA256, "engine": "llama.cpp",
                "engine_version": (runtime.stdout + runtime.stderr).strip(), "platform": platform.platform(),
                "python_version": platform.python_version(), "device_log": (devices.stdout + devices.stderr).splitlines(),
                "server_settings": {"host": "127.0.0.1", "ctx_size": 8192, "parallel": 4, "gpu_layers": "auto"},
                "system_prompt": SYSTEM, "count_rule": "len(text.split())", "service_policy_source": POLICY_URL,
                "service_selection": "Row 1518 asks about a specific purchase. Template row 12 was rhetorical.",
                "summaries": {row["task_id"]: attempts for row, attempts in results}, "service": service_attempt}
    save_json(destination / "hf_run.json", metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--generate", action="store_true", help="Run 161 fresh local completions. Defaults to outputs/hf_rerun/.")
    action.add_argument("--rebuild", action="store_true", help="Rebuild both result CSVs from saved model messages.")
    action.add_argument("--verify", action="store_true", help="Verify the saved results (default).")
    parser.add_argument("--server", type=Path, default=CACHE / "llama-b12211" / "llama-server.exe")
    parser.add_argument("--model", type=Path, default=CACHE / MODEL_FILENAME)
    parser.add_argument("--out", type=Path, help="Directory to generate, rebuild or verify.")
    parser.add_argument("--selection", type=Path, help="Optional JSON object mapping task IDs to selected references.")
    args = parser.parse_args()
    destination = args.out or (OUTPUTS / "hf_rerun" if args.generate else OUTPUTS)
    rows, service = inputs()
    if args.generate:
        destination.mkdir(parents=True, exist_ok=True)
        if (destination / "hf_run.json").exists():
            parser.exit(2, "A run is already saved here. Choose a fresh --out directory for generation.\n")
        metadata = generate_run(args, rows, service, destination)
    else:
        metadata = json.loads((destination / "hf_run.json").read_text(encoding="utf-8"))
    selection = metadata.get("selection")
    if args.selection:
        selection = json.loads(args.selection.read_text(encoding="utf-8-sig"))
    elif args.generate:
        # Only carry over previously checked sentences when their content hashes still match.
        selection = json.loads((OUTPUTS / "hf_run.json").read_text(encoding="utf-8")).get("selection")
    if not selection:
        parser.exit(2, "Supply --selection with the candidate/sentence references you reviewed. See LOCAL_HF.md.\n")
    try:
        tables = final_tables(metadata, rows, service, selection)
    except ValueError as error:
        if args.generate:
            parser.exit(2, f"Saved all fresh local messages in {destination}. {error}\n"
                           "Review the new messages and use --rebuild with --selection (see LOCAL_HF.md).\n")
        raise
    if args.generate or args.rebuild:
        with tempfile.TemporaryDirectory(dir=destination) as staging:
            for name, data in tables.items():
                write_csv(Path(staging) / name, data)
            for name in tables:
                os.replace(Path(staging) / name, destination / name)
        metadata["selection"] = selection
        save_json(destination / "hf_run.json", metadata)
    for name, expected in tables.items():
        if read_csv(destination / name) != expected:
            raise ValueError(f"{name} differs from the selected local messages.")
    print("Verified ten distinct sources over 100 words, ten 50-word summaries, and one traced service reply.")


if __name__ == "__main__":
    main()
