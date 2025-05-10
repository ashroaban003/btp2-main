import ast
import os
import sys
import subprocess
import json
from typing import List, Dict, Any, Set, Optional, Tuple
from github import Github
from openai import OpenAI
import requests
import json

def get_env_vars() -> Tuple[Optional[str], Optional[str]]:
    """Get GitHub token and repository name from environment variables."""
    token = os.getenv('GITHUB_TOKEN')
    repo = os.getenv('GITHUB_REPOSITORY')
    
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable is not set")
    if not repo:
        print("ERROR: GITHUB_REPOSITORY environment variable is not set")
    
    print(f"Environment check - Token present: {'Yes' if token else 'No'}, Repo present: {'Yes' if repo else 'No'}")
    return token, repo

def get_github_client() -> Optional[Github]:
    """Get authenticated GitHub client."""
    token, repo = get_env_vars()
    if not token or not repo:
        print("ERROR: Cannot create GitHub client - missing credentials")
        return None
    
    try:
        return Github(token)
    except Exception as e:
        print(f"ERROR: Failed to create GitHub client: {e}")
        return None

def get_file_content(file_path: str) -> str:
    """Get the current content of a file."""
    if not file_path or not isinstance(file_path, str):
        print("ERROR: Invalid file path provided")
        return None
        
    try:
        # First try to read directly from filesystem
        if os.path.exists(file_path):
            print(f"Reading file directly from filesystem: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    print(f"WARNING: File {file_path} is empty")
                return content
        else:
            print(f"File not found in filesystem: {file_path}")
    except Exception as e:
        print(f"Error reading file directly: {e}")
    
    # Try GitHub API if we have a token
    token, repo = get_env_vars()
    if token and repo:
        try:
            print(f"Attempting to get file content using GitHub API: {file_path}")
            g = Github(token)
            repo_obj = g.get_repo(repo)
            content = repo_obj.get_contents(file_path, ref="HEAD").decoded_content.decode('utf-8')
            if not content:
                print(f"WARNING: GitHub API returned empty content for {file_path}")
            return content
        except Exception as e:
            print(f"Error getting file content from GitHub API: {e}")
    
    # Fallback to git show
    try:
        print(f"Attempting to get file content using git show: {file_path}")
        result = subprocess.run(['git', 'show', f'HEAD:{file_path}'], 
                              capture_output=True, text=True, check=True)
        content = result.stdout
        if not content:
            print(f"WARNING: Git show returned empty content for {file_path}")
        return content
    except subprocess.CalledProcessError as e:
        print(f"Error getting file content from git: {e}")
        return None

def get_previous_content(file_path: str) -> str:
    """Get the previous version of a file from git."""
    if not file_path or not isinstance(file_path, str):
        print("ERROR: Invalid file path provided")
        return None
        
    # Try GitHub API if we have a token
    token, repo = get_env_vars()
    if token and repo:
        try:
            print(f"Attempting to get previous version using GitHub API: {file_path}")
            g = Github(token)
            repo_obj = g.get_repo(repo)
            # Get the previous commit
            commits = repo_obj.get_commits(path=file_path)
            if commits.totalCount > 1:
                prev_commit = commits[1]
                content = repo_obj.get_contents(file_path, ref=prev_commit.sha).decoded_content.decode('utf-8')
                if not content:
                    print(f"WARNING: Previous version of {file_path} is empty")
                print("Successfully retrieved previous version from GitHub API")
                return content
        except Exception as e:
            print(f"Error getting previous version from GitHub API: {e}")
    
    # Fallback to git show
    try:
        print(f"Attempting to get previous version from git: {file_path}")
        result = subprocess.run(['git', 'show', f'HEAD^:{file_path}'], 
                              capture_output=True, text=True, check=True)
        content = result.stdout
        if not content:
            print(f"WARNING: Previous version of {file_path} is empty")
        print("Successfully retrieved previous version from git")
        return content
    except subprocess.CalledProcessError as e:
        print(f"Error getting previous version from git: {e}")
        return None

def extract_api_elements(content: str) -> Dict[str, Dict[str, Any]]:
    """Extract API elements (functions, classes) from Python code with their signatures and docstrings."""
    if not content:
        return {}
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        print("Error parsing Python code")
        return {}
    
    elements = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Get function signature
            args = []
            for arg in node.args.args:
                arg_type = ast.unparse(arg.annotation) if arg.annotation else 'Any'
                args.append(f"{arg.arg}: {arg_type}")
            
            # Get return type
            return_type = ast.unparse(node.returns) if node.returns else 'Any'
            
            # Get docstring
            docstring = ast.get_docstring(node) or ""
            
            elements[node.name] = {
                'type': 'function',
                'signature': f"({', '.join(args)}) -> {return_type}",
                'docstring': docstring
            }
        elif isinstance(node, ast.ClassDef):
            # Get class docstring
            docstring = ast.get_docstring(node) or ""
            
            elements[node.name] = {
                'type': 'class',
                'docstring': docstring
            }
    
    return elements

def find_changes(old_elements: Dict[str, Dict[str, Any]], new_elements: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find changes between old and new API elements."""
    changes = []
    
    # Find added elements
    for name, element in new_elements.items():
        if name not in old_elements:
            changes.append({
                'type': 'added',
                'name': name,
                'description': f"New {element['type']} with signature: {element.get('signature', '')}"
            })
    
    # Find removed elements
    for name, element in old_elements.items():
        if name not in new_elements:
            changes.append({
                'type': 'removed',
                'name': name,
                'description': f"Removed {element['type']}"
            })
    
    # Find modified elements
    for name, new_element in new_elements.items():
        if name in old_elements:
            old_element = old_elements[name]
            if new_element['type'] != old_element['type']:
                changes.append({
                    'type': 'modified',
                    'name': name,
                    'description': f"Changed from {old_element['type']} to {new_element['type']}"
                })
            elif new_element.get('signature') != old_element.get('signature'):
                changes.append({
                    'type': 'modified',
                    'name': name,
                    'description': f"Signature changed from {old_element.get('signature', '')} to {new_element.get('signature', '')}"
                })
            elif new_element.get('docstring') != old_element.get('docstring'):
                changes.append({
                    'type': 'modified',
                    'name': name,
                    'description': "Docstring updated"
                })
    
    return changes

def create_readme_issue(py_file: str, changes: List[Dict[str, Any]]):
    """Create a GitHub issue about README updates needed."""
    token, repo_name = get_env_vars()
    if not token or not repo_name:
        print("ERROR: Cannot create issue - missing GitHub credentials")
        print("Would create issue with the following content:")
        print(f"Title: README Update Needed for {os.path.basename(py_file)}")
        print("Changes:")
        for change in changes:
            print(f"- {change['type'].title()}: {change['name']}")
        return
        
    try:
        g = get_github_client()
        if not g:
            return
            
        repo = g.get_repo(repo_name)
        print(f"Successfully connected to repository: {repo_name}")
        
        # Format changes for the issue
        changes_text = "\n".join([
            f"- {change['type'].title()}: {change['name']} ({change.get('description', '')})"
            for change in changes
        ])
        
        issue_title = f"README Update Needed for {os.path.basename(py_file)}"
        issue_body = f"""
The following changes in {py_file} require updates to the README.md file:

{changes_text}

Please review and update the README.md file to reflect these changes.
"""
        
        repo.create_issue(
            title=issue_title,
            body=issue_body,
            labels=["documentation", "readme"]
        )
        print(f"Successfully created issue: {issue_title}")
    except Exception as e:
        print(f"ERROR: Failed to create issue: {str(e)}")
        print("Would create issue with the following content:")
        print(f"Title: {issue_title}")
        print(f"Body: {issue_body}")

def create_api_failure_issue(file_path: str, changes: Dict[str, List[str]]) -> None:
    """Create a GitHub issue when API key fails."""
    try:
        # Get GitHub token and repository name
        token = get_github_token()
        repo_name = get_repo_name()
        
        # Initialize GitHub client
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        # Get file content
        content = get_file_content(file_path)
        if not content:
            print(f"Error: Could not get content for {file_path}")
            return
            
        # Extract function and class definitions
        tree = ast.parse(content)
        definitions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                definitions.append(node.name)
        
        # Format the issue body
        body = f"""# API Documentation Update Required

The following changes were detected in {file_path}:

## Changes Detected
{format_changes(changes)}

## Current Definitions
{chr(10).join(f'- {defn}' for defn in definitions)}

## Required Actions
1. Review the changes in {file_path}
2. Update the documentation to reflect these changes
3. Ensure all new functions/classes are properly documented

Note: This issue was created automatically because the OpenAI API key was not available for automatic documentation updates.

## Labels
- documentation
- help wanted
- good first issue
"""
        
        # Create the issue
        repo.create_issue(
            title=f"Documentation Update Required: {file_path}",
            body=body,
            labels=["documentation", "help wanted", "good first issue"]
        )
        print(f"Created issue for {file_path}")
        
    except Exception as e:
        print(f"Error creating issue: {str(e)}")

def create_github_issue(title: str, body: str) -> None:
    """Create a GitHub issue with the given title and body."""
    token, repo_name = get_env_vars()
    if not token or not repo_name:
        print("ERROR: Cannot create issue - missing GitHub credentials")
        print("Would create issue with the following content:")
        print(f"Title: {title}")
        print(f"Body:\n{body}")
        return
    
    try:
        g = get_github_client()
        if not g:
            print("ERROR: Failed to get GitHub client")
            return
            
        repo = g.get_repo(repo_name)
        print(f"Successfully connected to repository: {repo_name}")
        
        # Create issue with labels
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=["documentation", "help wanted", "good first issue"]
        )
        print(f"Successfully created issue #{issue.number}: {title}")
    except Exception as e:
        print(f"ERROR: Failed to create GitHub issue: {e}")
        print("Would create issue with the following content:")
        print(f"Title: {title}")
        print(f"Body:\n{body}")

def get_openai_client() -> Optional[OpenAI]:
    """Get authenticated OpenAI client."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set")
        return None

    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        print(f"ERROR: Failed to create OpenAI client: {e}")
        return None

def check_documentation(file_path: str, content: str) -> dict:
    """Check if documentation needs to be updated using OpenAI API."""
    try:
        API_KEY = os.getenv("GEMINI_API_KEY")  # replace with your actual key
        API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "contents": [
                {
                    "parts": [
                        {"text": "hey"}
                    ]
                }
            ]
        }

        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
            
        prompt = f"""Analyze the following Python code and determine if documentation needs to be updated in concise form.
        Return a JSON response with two fields:
        1. change_required: boolean indicating if documentation needs to be updated
        2. updated_doc: string containing the updated documentation if change_required is true, null otherwise

        Code:
        {content}

        Current documentation:
        {get_current_documentation(file_path)}

        Return only the JSON response, no other text."""

        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        
        try:
           result = response.json()
           output = result["candidates"][0]["content"]["parts"][0]["text"]
           return output
        except json.JSONDecodeError:
            print("ERROR: Failed to parse LLM response as JSON")
            return {"change_required": True, "updated_doc": None}
            
    except Exception as e:
        print(f"ERROR: Failed to check documentation: {e}")
        return {"change_required": True, "updated_doc": None}

def analyze_changes(file_path: str) -> None:
    """Analyze changes between current and previous versions of a file."""
    if not file_path or not isinstance(file_path, str):
        print("ERROR: Invalid file path provided")
        return
        
    print(f"Analyzing changes for {file_path}")
    
    try:
        current_content = get_file_content(file_path)
        if not current_content:
            error_msg = f"Could not read current content of {file_path}"
            print(error_msg)
            create_github_issue(
                f"Error: Failed to analyze {os.path.basename(file_path)}",
                f"Error message: {error_msg}\n\nPlease check if the file exists and has content."
            )
            return
        
        # Check if documentation needs to be updated
        doc_check = check_documentation(file_path, current_content)
        if not doc_check["change_required"]:
            print("No documentation changes required")
            return
            
        previous_content = get_previous_content(file_path)
        if not previous_content:
            print(f"No previous version found for {file_path}, treating as new file")
            current_elements = extract_api_elements(current_content)
            if current_elements:
                title = f"Documentation Update Needed for {file_path}"
                body = f"The file {file_path} has been modified. Please review and update the documentation for the following changes:\n\n"
                for name, element in current_elements.items():
                    if element['type'] == 'function':
                        body += f"python\n{name}{element['signature']}\n"
                        if element['docstring']:
                            body += f'"""{element["docstring"]}"""\n'
                        body += "\n\n"
                body += "This is an automated issue created because the OpenAI API key is not available. Please manually update the documentation as needed.\n\n"
                body += "Steps to Update Documentation:\n"
                body += f"1. Review the changes in {file_path}\n"
                body += f"2. Update the corresponding documentation in src/api/{os.path.splitext(os.path.basename(file_path))[0]}.md\n"
                body += "3. Create a pull request with the documentation updates"
                create_github_issue(title, body)
            return
        
        current_elements = extract_api_elements(current_content)
        previous_elements = extract_api_elements(previous_content)
        
        changes = find_changes(previous_elements, current_elements)
        
        if not changes:
            print("No API changes detected")
            return
        
        print("Changes detected:")
        for change in changes:
            print(f"{change['type'].title()}: {change['name']} - {change['description']}")
        
        title = f"Documentation Update Needed for {file_path}"
        body = f"The file {file_path} has been modified. Please review and update the documentation for the following changes:\n\n"
        
        for change in changes:
            if change['type'] == 'added' and change['name'] in current_elements:
                element = current_elements[change['name']]
                if element['type'] == 'function':
                    body += f"python\n{change['name']}{element['signature']}\n"
                    if element['docstring']:
                        body += f'"""{element["docstring"]}"""\n'
                    body += "\n\n"
        
        body += "This is an automated issue created because the OpenAI API key is not available. Please manually update the documentation as needed.\n\n"
        body += "Steps to Update Documentation:\n"
        body += f"1. Review the changes in {file_path}\n"
        body += f"2. Update the corresponding documentation in src/api/{os.path.splitext(os.path.basename(file_path))[0]}.md\n"
        body += "3. Create a pull request with the documentation updates"
        
        create_github_issue(title, body)
        
    except Exception as e:
        error_msg = f"Error analyzing changes: {str(e)}"
        print(error_msg)
        create_github_issue(
            f"Error: Failed to analyze {os.path.basename(file_path)}",
            f"Error message: {error_msg}\n\nPlease check the file and try again."
        )

def get_current_documentation(file_path: str) -> str:
    """Get current documentation from the API folder."""
    doc_path = f"src/api/{os.path.splitext(os.path.basename(file_path))[0]}.md"
    try:
        if os.path.exists(doc_path):
            with open(doc_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"Error reading documentation: {e}")
    return "No existing documentation found."

if _name_ == '_main_':
    if len(sys.argv) != 2:
        print("Usage: python analyze_py_changes.py <file_path>")
        sys.exit(1)
    
    analyze_changes(sys.argv[1])