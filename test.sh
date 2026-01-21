#!/bin/bash
# Test script for the RAG workflow

echo "Testing Superpower Coach RAG Workflow..."
echo "========================================="
echo

# Test 1: Basic JSON output
echo "Test 1: Basic workflow with example input"
python3 rag_workflow.py --input example_input.json --format json > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Basic workflow test passed"
else
    echo "✗ Basic workflow test failed"
    exit 1
fi

# Test 2: Full prompt generation
echo "Test 2: Full prompt generation with RAG output"
python3 rag_workflow.py \
    --input example_input.json \
    --format prompt \
    --output test_output.txt \
    --rag-output test_rag.json > /dev/null 2>&1
if [ $? -eq 0 ] && [ -f test_output.txt ] && [ -f test_rag.json ]; then
    echo "✓ Full prompt generation test passed"
    echo "  - Generated test_output.txt ($(wc -l < test_output.txt) lines)"
    echo "  - Generated test_rag.json ($(stat -f%z test_rag.json 2>/dev/null || stat -c%s test_rag.json) bytes)"
else
    echo "✗ Full prompt generation test failed"
    exit 1
fi

echo
echo "All tests passed! ✓"
echo
echo "Check these files:"
echo "  - test_output.txt (combined prompt)"
echo "  - test_rag.json (RAG protocol details)"
echo
echo "To clean up test files: rm test_*.txt test_*.json"
