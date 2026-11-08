# Local Hugging Face generation

The Python script starts llama.cpp on the same machine, verifies the SHA-256 of the downloaded weights and sends the review text to its loopback address. Python 3.11 or newer is required. The project used the Windows x64 Vulkan build on an NVIDIA GeForce RTX 2070.

## Verify the saved results

From PowerShell in `1 Code`, run the following. Verification uses the saved model messages, the original review data and the recorded selections. It works without downloading the weights.

```powershell
.\.venv\Scripts\python.exe phase2_local_hf.py --verify
```

To reconstruct the two result CSVs from the saved model messages, use `--rebuild`. This verifies that the source text matches the original prompts, each summary has exactly 50 whitespace-separated words, the selected words match the recorded SHA-256 hash, and the CSV entries match the reconstructed text.

## Run the model again

The model and inference program are already installed under `$env:USERPROFILE\.cache\COMP262-HF` on the project computer. Start a fresh run with the following command. Supply a new output directory for each run.

```powershell
.\.venv\Scripts\python.exe phase2_local_hf.py --generate --out outputs/hf_rerun
```

The script generates 16 candidate paragraphs for each review and one service reply. It writes all raw messages to `hf_run.json` in the new run directory. If the previously selected sentences reproduce byte for byte, the script also writes and verifies both result CSVs. Sampling and backend differences can change text despite a fixed seed. For changed results, review the new candidates and supply the references as described below.

## First run on another Windows x64 PC

Use PowerShell to download Qwen's 2.1 GB model file and the pinned llama.cpp runtime. A Vulkan-capable graphics driver supports the configuration used here.

```powershell
$hfCache = Join-Path $env:USERPROFILE ".cache\COMP262-HF"
$null = New-Item -ItemType Directory -Force -Path $hfCache
$modelPath = Join-Path $hfCache "qwen2.5-3b-instruct-q4_k_m.gguf"
$runtimeZip = Join-Path $hfCache "llama-b12211-bin-win-vulkan-x64.zip"

curl.exe -fL --retry 3 "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/7dabda4d13d513e3e842b20f0d435c732f172cbe/qwen2.5-3b-instruct-q4_k_m.gguf" -o $modelPath
if ($LASTEXITCODE -ne 0) { throw "Model download failed" }
curl.exe -fL --retry 3 "https://github.com/ggml-org/llama.cpp/releases/download/b12211/llama-b12211-bin-win-vulkan-x64.zip" -o $runtimeZip
if ($LASTEXITCODE -ne 0) { throw "Runtime download failed" }
if ((Get-FileHash -LiteralPath $runtimeZip).Hash -ne "20954cbad1a4626436c6ebaed5e48477f68427b075934689f360301ac426a2f1") { throw "Runtime checksum mismatch" }
Expand-Archive -LiteralPath $runtimeZip -DestinationPath (Join-Path $hfCache "llama-b12211") -Force
.\.venv\Scripts\python.exe phase2_local_hf.py --generate --out outputs/hf_rerun
```

`--model` and `--server` accept explicit file paths for other cache locations. Keep the project's existing `outputs/hf_summary_inputs_TEMPLATE.csv` and `outputs/reviews_clean.csv` alongside the script even if you choose another destination for the results.

## Reading and selecting results

- `outputs/hf_summaries.csv` contains all ten reviews, all ten selected summaries, the source and output word counts, the selection references and a technical quality note for each example. The recorded selection uses complete model paragraphs for tasks 4 and 7. The other eight summaries join complete, unedited sentences from several drafts for the same review.
- `outputs/hf_service_response.csv` pairs the question from row 1518 with a single local completion. Template row 12 speculates about the recipient's reaction. Row 1518 instead asks whether a specific gift card works on Amazon. The service prompt includes the issuer's redemption terms.
- `outputs/hf_run.json` records the model revision and checksum, inference settings, device, prompts, all 161 raw model messages and request timings. The first eight candidate paragraphs for each review used a 50-word decoding grammar. The next eight used the same prompt without the grammar. Some rejected drafts repeat words or end awkwardly. Source accuracy and readability guided the final choice of material.

A selection such as `15.1 1.2 7.3` takes candidate 15's first sentence, candidate 1's second sentence and candidate 7's third sentence, in that order. A single integer takes the entire candidate. The stored selections use one-based indexes. The code splits candidate sentences at whitespace immediately following a period, question mark or exclamation point.

If fresh generations differ, copy the `selection` object from `outputs/hf_run.json` to a new JSON file, keep all ten task entries, and replace the references and notes after checking the new drafts. Remove the old `sha256` values when selecting different text. For example, one task entry can be `"1": {"references": "15.1 1.2 7.3", "note": "Describe what you checked."}`. Rebuild with the file you edited, then verify.

```powershell
.\.venv\Scripts\python.exe phase2_local_hf.py --rebuild --out outputs/hf_rerun --selection my_selection.json
.\.venv\Scripts\python.exe phase2_local_hf.py --verify --out outputs/hf_rerun
```

The model weights and inference runtime are available from [Qwen on Hugging Face](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/tree/7dabda4d13d513e3e842b20f0d435c732f172cbe) and the [llama.cpp b12211 release](https://github.com/ggml-org/llama.cpp/releases/tag/b12211). The service response uses the [Whole Foods Market gift card redemption terms](https://www.wholefoodsmarket.com/legal/gift-cards-terms-and-conditions).
