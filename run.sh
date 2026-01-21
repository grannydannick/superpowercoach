#!/bin/bash
set -e

echo "=========================================="
echo "Superpower Coach - Email Generator"
echo "=========================================="
echo

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo
    echo "To generate emails, you need an OpenAI API key."
    echo "Create a .env file with your API key:"
    echo
    echo "  OPENAI_API_KEY=sk-your-key-here"
    echo "  OPENAI_MODEL=gpt-4o-mini"
    echo
    echo "For now, I'll just generate the prompt without emails."
    echo
    GENERATE_EMAILS=false
else
    # Load API key from .env
    source .env
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_api_key_here" ]; then
        echo "⚠️  Please add your real API key to .env file"
        echo
        GENERATE_EMAILS=false
    else
        echo "✓ API key found!"
        echo
        GENERATE_EMAILS=true
    fi
fi

# Run the workflow
echo "Running workflow with example patient data..."
echo "  - 45 year old male"
echo "  - Metabolic concerns (elevated HbA1c, triglycerides)"
echo "  - Goals: Energy and weight loss"
echo

if [ "$GENERATE_EMAILS" = true ]; then
    python3 rag_workflow.py \
        --input example_input.json \
        --output combined_prompt.txt \
        --rag-output rag_details.json \
        --generate-emails \
        --emails-output generated_emails.txt

    echo
    echo "=========================================="
    echo "✅ Success! Generated files:"
    echo "=========================================="
    echo "  📄 combined_prompt.txt   - The prompt sent to the LLM"
    echo "  📊 rag_details.json      - Retrieved protocol details"
    echo "  📧 generated_emails.txt  - YOUR COMPLETE EMAIL SERIES!"
    echo
    echo "Open generated_emails.txt to see the 30-day email series!"
else
    python3 rag_workflow.py \
        --input example_input.json \
        --output combined_prompt.txt \
        --rag-output rag_details.json

    echo
    echo "=========================================="
    echo "✅ Generated (without LLM):"
    echo "=========================================="
    echo "  📄 combined_prompt.txt   - Ready to send to an LLM"
    echo "  📊 rag_details.json      - Retrieved protocol details"
    echo
    echo "To generate actual emails, add your API key to .env file"
fi
