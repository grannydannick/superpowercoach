# RAG Workflow

This repo wires a simple RAG step over `protocols.txt` and feeds the results
into `prompt.txt` to generate the 30-day email series.

## How It Works

1. Load member input data.
2. Retrieve matching protocol sections from `protocols.txt`.
3. Attach protocol details as `[PD]` and build the final prompt input.
4. Send the combined prompt to your LLM.

## Input Shape (JSON)

Use either `PRO` or `selected_protocols` as the list of the top 3 protocols.

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
    },
    {
      "rank": 2,
      "theme": "Cardiovascular",
      "protocol_name": "Cardiovascular Health Protocol",
      "evidence_source": "Biomarker"
    },
    {
      "rank": 3,
      "theme": "Foundations of Health",
      "protocol_name": "Foundations of Health Protocol",
      "evidence_source": "Foundations"
    }
  ]
}
```

## Run

```sh
python rag_workflow.py \
  --input /absolute/path/to/input.json \
  --format prompt \
  --output /absolute/path/to/combined_prompt.txt \
  --rag-output /absolute/path/to/rag_protocols.json
```

The `combined_prompt.txt` output is ready to send to your LLM.

## Free-Text Synthetic Input

Set your API key (OpenAI-compatible) and generate a synthetic input JSON from
free text, then continue through RAG.

```sh
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-4o-mini

python rag_workflow.py \
  --free-text "33 year old female focused on weight loss" \
  --synthetic-output /absolute/path/to/synthetic_input.json \
  --output /absolute/path/to/combined_prompt.txt
```

Or create a `.env` file (recommended, gitignored):

```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```
