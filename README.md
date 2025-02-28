# Programming Problem Solutions Generator

This web application generates programming solutions for OmegaUp problems using OpenAI's API.

## Features

- Fetch problem details from OmegaUp API
- Generate detailed solutions with explanations using OpenAI
- Support for multiple programming languages
- Markdown rendering of solutions

## Setup Instructions

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

4. Run the application:
```bash
python app.py
```

The application will be available at `http://127.0.0.1:5001/`

## Deployment to Vercel

This project includes a `vercel.json` configuration file for easy deployment to Vercel:

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Deploy to Vercel:
```bash
vercel
```

3. Set environment variables in the Vercel dashboard:
   - OPENAI_API_KEY
   - FLASK_SECRET_KEY

## Project Structure

- `app.py`: Main Flask application
- `api_client.py`: API clients for OmegaUp and OpenAI
- `prompts.txt`: System prompt for OpenAI
- `templates/`: HTML templates
- `static/css/`: CSS stylesheets
- `requirements.txt`: Project dependencies
- `vercel.json`: Vercel deployment configuration 