# Quick Start Guide (For Beginners!)

Welcome! This guide will help you generate personalized health coaching emails in just 2 steps.

## Step 1: Get an API Key (Optional but Recommended)

To generate the actual emails, you need an OpenAI API key:

1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (it looks like: `sk-proj-...`)

## Step 2: Set Up Your API Key

Create a file called `.env` in this folder:

```bash
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

**Important:** Replace `sk-proj-your-key-here` with your actual API key!

## Step 3: Run the Program

Just run this single command:

```bash
./run.sh
```

That's it! 🎉

## What You'll Get

After running, you'll see these files:

- **`generated_emails.txt`** ← This is what you want! Open it to see the 5 personalized emails
- `combined_prompt.txt` - The instructions sent to the AI
- `rag_details.json` - The protocol details that were retrieved

## Without an API Key?

If you don't have an API key yet, the program will still:
- Generate the prompt and retrieve protocols
- Create `combined_prompt.txt` that you can copy/paste into ChatGPT manually

## Customize the Input

Want to test with different patient data? Edit `example_input.json` to change:
- Age, sex, lifestyle
- Biomarker values
- Health goals
- Protocols to recommend

Then run `./run.sh` again!

## Need Help?

- Check `README.md` for advanced usage
- Run `python3 rag_workflow.py --help` for all options
- The test suite: `./test.sh`

## Common Issues

**"Permission denied"**
```bash
chmod +x run.sh
./run.sh
```

**"python3: command not found"**
- You need Python 3 installed
- Try `python` instead of `python3`

**API key doesn't work**
- Make sure it starts with `sk-`
- Check there are no extra spaces in your .env file
- Make sure the .env file is in the same folder as run.sh
