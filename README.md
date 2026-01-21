# Superpower Coach RAG Workflow

This project builds a retrieval-augmented workflow that:

- Ingests member input (biomarkers, preferences, context, top protocols).
- Retrieves protocol recommendations from `protocols.txt`.
- Feeds everything into `prompt.txt` to generate a 30-day email series.

## 🚀 Quick Start (For Beginners)

**New to coding? Want the easiest way to run this?**

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Create a `.env` file with your key (copy from `.env.example`)
3. Run: `./run.sh`

See **[QUICKSTART.md](QUICKSTART.md)** for step-by-step beginner instructions!

## Files

- `prompt.txt`: The email-generation prompt and formatting rules.
- `analysis_flow.txt`: How protocols are determined from member data.
- `protocols.txt`: Protocol library and recommendations.
- `rag_workflow.py`: RAG pipeline + optional synthetic input generation.
- `workflow.md`: Usage notes.
- `example_input.json`: Example input file to get started.
- `test.sh`: Test script to verify everything works.

## Quick Test

Run the included test script to verify everything is working:

```sh
./test.sh
```

This will generate `test_output.txt` and `test_rag.json` for inspection.

## Basic Usage

Use the example input file:

```sh
python3 rag_workflow.py \
  --input example_input.json \
  --format prompt \
  --output combined_prompt.txt \
  --rag-output rag_protocols.json
```

Or use your own input file:

```sh
python3 rag_workflow.py \
  --input /path/to/your_input.json \
  --format prompt \
  --output combined_prompt.txt \
  --rag-output rag_protocols.json
```

The `combined_prompt.txt` output is ready to send to your LLM.

## Generate Actual Email Series

To generate the complete 30-day email series (5 emails), use the `--generate-emails` flag:

```sh
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-4o-mini

python rag_workflow.py \
  --input example_input.json \
  --generate-emails \
  --emails-output email_series.txt
```

This sends the combined prompt to the LLM and generates the actual coaching emails.

## Free-Text Synthetic Input

This mode uses an OpenAI-compatible API to turn free text into a synthetic
member input JSON, then runs the RAG flow.

```sh
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-4o-mini

python rag_workflow.py \
  --free-text "33 year old female focused on weight loss" \
  --synthetic-output /absolute/path/to/synthetic_input.json \
  --output /absolute/path/to/combined_prompt.txt
```

You can also combine `--free-text` with `--generate-emails` to go from free text all the way to generated emails:

```sh
python rag_workflow.py \
  --free-text "33 year old female focused on weight loss" \
  --generate-emails \
  --emails-output email_series.txt
```

Or create a `.env` file (recommended, gitignored):

```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

Optional env vars:

- `OPENAI_API_BASE` (default: `https://api.openai.com`)
- `OPENAI_MODEL` (default: `gpt-4o-mini`)
- `OPENAI_API_KEY` (required for `--free-text` and `--generate-emails`)

## Input Shape

Your input JSON should include the top 3 protocols:

```json
{
  "B": { "biomarker_summary": "..." },
  "P": { "preferences": ["Energy", "Weight Loss"] },
  "C": { "age": 45, "sex": "M" },
  "PRO": [
    {
      "rank": 1,
      "theme": "Metabolic/Insulin Resistance",
      "protocol_name": "Metabolic Reset Protocol",
      "evidence_source": "Biomarker"
    }
  ]
}
```
