import requests
import json
from openai import OpenAI
import os
import traceback
from dotenv import load_dotenv
import openai
import sys

# Load environment variables
load_dotenv()

print(f"Python version: {sys.version}")
print(f"OpenAI package version: {openai.__version__}")

class OmegaUpClient:
    """Client for interacting with the OmegaUp API"""
    
    BASE_URL = "https://omegaup.com/api"
    
    @staticmethod
    def get_problem_details(problem_alias):
        """
        Fetch problem details from OmegaUp API
        
        Args:
            problem_alias (str): The alias of the problem to fetch
            
        Returns:
            dict: Processed problem data or None if there was an error
        """
        try:
            url = f"{OmegaUpClient.BASE_URL}/problem/details/?problem_alias={problem_alias}"
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            data = response.json()
            
            # Extract the problem statement from the response
            statement_data = data.get('statement', {})
            markdown_content = statement_data.get('markdown', '')
            
            # Extract additional parameters
            limits = {}
            limits['TimeLimit'] = data.get('time_limit', 'Not specified')
            limits['MemoryLimit'] = data.get('memory_limit', 'Not specified')
            limits['OutputLimit'] = data.get('output_limit', 'Not specified')
            limits['OverallWallTimeLimit'] = data.get('overall_wall_time_limit', 'Not specified')
            limits['ExtraWallTime'] = data.get('extra_wall_time', 'Not specified')
            
            # Extract sample cases if available
            sample_cases = []
            if 'sample_cases' in data:
                sample_cases = data.get('sample_cases', [])
            
            # Process the problem data
            problem_data = {
                'problem_title': data.get('title', 'Unknown Title'),
                'problem_alias': problem_alias,
                'problem_description': markdown_content,
                'examples': sample_cases,
                'constraints': [],  # We'll need to extract these from the statement
                'limits': limits,
                'input_format': data.get('input_format', 'Not specified'),
                'output_format': data.get('output_format', 'Not specified')
            }
            
            return problem_data
            
        except requests.exceptions.RequestException:
            return None
        except json.JSONDecodeError:
            return None
        except Exception:
            return None


class OpenAIClient:
    """Client for interacting with the OpenAI API"""
    
    @staticmethod
    def generate_solution(problem_data, language):
        """
        Generate a solution for a problem using OpenAI
        
        Args:
            problem_data (dict): Problem details
            language (str): Programming language for the solution
            
        Returns:
            dict: Generated solution data or None if there was an error
        """
        try:
            # Create a prompt for OpenAI
            prompt = OpenAIClient._create_prompt(problem_data, language)
            
            # Get API key from environment
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return None
            
            # Create a clean OpenAI client instance
            client = OpenAI()
            client.api_key = api_key
            
            # Load system prompt from prompts.txt file
            system_prompt = ""
            try:
                with open('prompts.txt', 'r') as file:
                    system_prompt = file.read().strip()
            except Exception:
                # Fallback to default system prompt
                system_prompt = "You are an expert competitive programmer who provides clear explanations and efficient solutions to programming problems. Format your entire response in Markdown."
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            # Process the response
            solution_text = response.choices[0].message.content
            
            # For markdown format, we just return the entire content
            if problem_data.get('markdown_format', False):
                return {
                    'solution_content': solution_text
                }
            
            # Otherwise, parse the solution text to extract explanation, code, and complexity
            solution_data = OpenAIClient._parse_solution(solution_text, language)
            
            return solution_data
            
        except Exception as e:
            traceback.print_exc()
            return None
    
    @staticmethod
    def _create_prompt(problem_data, language):
        """Create a prompt for OpenAI based on problem data and language"""
        
        # Truncate problem description if it's too long (to avoid token limit issues)
        problem_description = problem_data['problem_description']
        if len(problem_description) > 8000:  # Arbitrary limit to avoid token limit issues
            problem_description = problem_description[:8000] + "...\n[Description truncated due to length]"
        
        # Format limits information
        limits_info = ""
        if 'limits' in problem_data and problem_data['limits']:
            limits = problem_data['limits']
            limits_info = "LIMITS:\n"
            for key, value in limits.items():
                limits_info += f"- {key}: {value}\n"
        
        # Format input/output format
        io_format = ""
        if problem_data.get('input_format') or problem_data.get('output_format'):
            io_format = "INPUT/OUTPUT FORMAT:\n"
            if problem_data.get('input_format'):
                io_format += f"Input: {problem_data.get('input_format')}\n"
            if problem_data.get('output_format'):
                io_format += f"Output: {problem_data.get('output_format')}\n"
        
        # Format sample cases
        sample_cases = ""
        if problem_data.get('examples') and len(problem_data['examples']) > 0:
            sample_cases = "SAMPLE CASES:\n"
            for i, case in enumerate(problem_data['examples']):
                sample_cases += f"Example {i+1}:\n"
                if 'input' in case:
                    sample_cases += f"Input: {case['input']}\n"
                if 'output' in case:
                    sample_cases += f"Output: {case['output']}\n"
                if 'explanation' in case and case['explanation']:
                    sample_cases += f"Explanation: {case['explanation']}\n"
                sample_cases += "\n"
        
        # Check if markdown format is requested
        if problem_data.get('markdown_format', False):
            prompt = f"""
I need a solution to the following programming problem:

PROBLEM TITLE: {problem_data['problem_title']}

PROBLEM DESCRIPTION:
{problem_description}

{io_format}

{limits_info}

{sample_cases}

Please provide a complete solution in Markdown format that includes:
1. A clear and detailed explanation of your approach with a heading "## Approach"
   - Include step-by-step description of the solution
   - Justify each step in your approach
   - Explain key concepts and algorithms used
   - Make your explanation easy to understand for programming students

2. An efficient solution in {language} with a heading "## Solution" and code in a properly formatted code block with syntax highlighting
   - Your code must be well-commented
   - Your code must pass all test cases
   - Your code must comply with the time and memory limits

3. Time and space complexity analysis with a heading "## Complexity Analysis"
   - Provide detailed analysis of both time and space complexity
   - Explain why your solution meets the required constraints

Your entire response should be in well-formatted Markdown with proper headings (using ## for main sections), code blocks with syntax highlighting for {language} (using ```{language.lower()} and ```), and clear explanations.

DO NOT use HTML tags in your response, only use Markdown syntax.
"""
        else:
            prompt = f"""
I need a solution to the following programming problem:

PROBLEM TITLE: {problem_data['problem_title']}

PROBLEM DESCRIPTION:
{problem_description}

{io_format}

{limits_info}

{sample_cases}

Please provide:
1. A detailed explanation of your approach that includes:
   - Step-by-step description of the solution
   - Justification for each step
   - Explanation of key concepts and algorithms used
   - Make your explanation easy to understand for programming students

2. An efficient solution in {language} that:
   - Is well-commented
   - Passes all test cases
   - Complies with the time and memory limits

3. Detailed time and space complexity analysis that:
   - Explains why your solution meets the required constraints
   - Provides the Big O notation with explanation

Format your response as follows:
```explanation
Your detailed explanation here...
```

```code
Your {language} code here...
```

```complexity
Time Complexity: O(?) - with explanation
Space Complexity: O(?) - with explanation
```
"""
        return prompt
    
    @staticmethod
    def _parse_solution(solution_text, language):
        """Parse the solution text from OpenAI to extract components"""
        
        # Initialize default values
        explanation = ""
        code = ""
        time_complexity = "O(n)"  # Default value
        space_complexity = "O(n)"  # Default value
        
        # Extract explanation
        if "```explanation" in solution_text and "```" in solution_text.split("```explanation", 1)[1]:
            explanation = solution_text.split("```explanation", 1)[1].split("```", 1)[0].strip()
        else:
            # Fallback: try to extract explanation from the beginning of the text
            explanation = solution_text.split("```code", 1)[0].strip()
        
        # Extract code
        if "```code" in solution_text and "```" in solution_text.split("```code", 1)[1]:
            code = solution_text.split("```code", 1)[1].split("```", 1)[0].strip()
        elif f"```{language}" in solution_text.lower():
            # Alternative format: ```python instead of ```code
            code = solution_text.split(f"```{language}", 1)[1].split("```", 1)[0].strip()
        elif "```" in solution_text:
            # Fallback: just get the first code block
            code = solution_text.split("```", 2)[1].strip()
            if code.lower().startswith(language):
                code = code[len(language):].strip()
        
        # Extract complexity
        if "```complexity" in solution_text and "```" in solution_text.split("```complexity", 1)[1]:
            complexity_text = solution_text.split("```complexity", 1)[1].split("```", 1)[0].strip()
            
            # Extract time complexity
            if "Time Complexity:" in complexity_text:
                time_part = complexity_text.split("Time Complexity:", 1)[1].strip()
                time_complexity = time_part.split("\n", 1)[0].strip()
            
            # Extract space complexity
            if "Space Complexity:" in complexity_text:
                space_part = complexity_text.split("Space Complexity:", 1)[1].strip()
                space_complexity = space_part.split("\n", 1)[0].strip()
        
        return {
            'solution_explanation': explanation,
            'solution_code': code,
            'solution_complexity': {
                'time': time_complexity,
                'space': space_complexity
            }
        }
