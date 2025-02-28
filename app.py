from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
import secrets
import traceback
import markdown
from api_client import OmegaUpClient, OpenAIClient

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get secret key from environment variable or generate a random one
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
# Add Markdown filter to Jinja2
app.jinja_env.filters['markdown'] = lambda text: markdown.markdown(text, extensions=['extra', 'codehilite'])

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/generate', methods=['POST'])
def generate():
    problem_alias = request.form.get('problem_alias')
    language = request.form.get('language')
    
    try:
        # 1. Fetch problem details from OmegaUp API
        app.logger.info(f"Fetching problem details for alias: {problem_alias}")
        problem_data = OmegaUpClient.get_problem_details(problem_alias)
        
        if not problem_data:
            app.logger.error(f"Failed to fetch problem details for alias: {problem_alias}")
            flash(f'Error: Could not fetch problem details for "{problem_alias}". Please check the problem alias and try again.', 'error')
            return redirect(url_for('home'))
        
        app.logger.info(f"Successfully fetched problem details: {problem_data.get('problem_title')}")
        
        # 2. Generate solution using OpenAI
        app.logger.info(f"Generating solution in {language}")
        
        # Update the prompt to request markdown format
        problem_data['markdown_format'] = True
        solution_data = OpenAIClient.generate_solution(problem_data, language)
        
        if not solution_data:
            app.logger.error("Failed to generate solution with OpenAI")
            flash('Error: Could not generate solution. Please try again later.', 'error')
            return redirect(url_for('home'))
        
        app.logger.info("Successfully generated solution")
        
        # Combine problem and solution data
        result_data = {
            'problem_title': problem_data.get('problem_title', 'Unknown Title'),
            'problem_alias': problem_alias,
            'language': language.capitalize(),
            'solution_content': solution_data.get('solution_content', ''),
        }
        
        # Render the solution page directly
        return render_template('solution.html', **result_data)
        
    except Exception as e:
        app.logger.error(f"Exception in generate route: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run() 