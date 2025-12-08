# flask_app/utils/openai_service.py

import os
import json
import pdfplumber
from flask import current_app
from openai import OpenAI
from typing import Dict, Optional, Tuple

# Try to import OpenAI exception classes (structure varies by version)
try:
    from openai import APIError, RateLimitError, APIConnectionError, APITimeoutError, APIStatusError
except ImportError:
    try:
        # Try alternative import structure
        from openai.error import APIError, RateLimitError, APIConnectionError, APITimeoutError
        APIStatusError = APIError
    except ImportError:
        # Fallback - use generic Exception
        APIError = Exception
        RateLimitError = Exception
        APIConnectionError = Exception
        APITimeoutError = Exception
        APIStatusError = Exception

def extract_text_from_pdf(pdf_data: bytes) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract text from PDF file data.
    
    Args:
        pdf_data: Binary PDF data
        
    Returns:
        Tuple of (extracted_text, error_message)
    """
    try:
        import io
        
        # Create a file-like object from bytes
        pdf_file = io.BytesIO(pdf_data)
        
        # Extract text from all pages
        text_parts = []
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        extracted_text = '\n\n'.join(text_parts)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            return None, "PDF appears to be empty or contains no extractable text."
        
        return extracted_text, None
        
    except Exception as e:
        current_app.logger.error(f"Error extracting text from PDF: {str(e)}")
        return None, f"Error extracting text from PDF: {str(e)}"


def chunk_text(text: str, max_chunk_size: int = 100000) -> list:
    """
    Split text into chunks if it exceeds the maximum size.
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Try to split on paragraphs first
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
            current_chunk += paragraph + '\n\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # If a single paragraph is too large, split it by sentences
            if len(paragraph) > max_chunk_size:
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 2 <= max_chunk_size:
                        current_chunk += sentence + '. '
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + '. '
            else:
                current_chunk = paragraph + '\n\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def generate_research_brief(text: str, model: str = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Generate a research brief from text using OpenAI API.
    
    Args:
        text: Source text to generate brief from
        model: OpenAI model to use (defaults to config)
        
    Returns:
        Tuple of (brief_data_dict, error_message)
        brief_data_dict contains: title, citation, summary (bullet points)
    """
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return None, "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        
        if not model:
            model = os.environ.get('OPENAI_MODEL', 'gpt-4-turbo')
        
        client = OpenAI(api_key=api_key)
        
        # Prepare the prompt
        prompt = f"""Analyze the following text and generate a research brief in JSON format with the following structure:
{{
    "title": "A concise, descriptive title for this research (max 200 characters)",
    "citation": "A properly formatted citation for this source (author, title, publication, date if available, or general format)",
    "summary": "A bullet-point summary of the key findings, main points, and important information. Use bullet points separated by newlines (\\n). Keep it comprehensive but concise."
}}

Text to analyze:
{text[:150000]}"""  # Limit to ~150k chars to leave room for prompt and response
        
        # Call OpenAI API with structured output
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a research assistant that creates structured research briefs from academic and professional texts. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse the response
        response_text = response.choices[0].message.content
        brief_data = json.loads(response_text)
        
        # Validate required fields
        required_fields = ['title', 'citation', 'summary']
        for field in required_fields:
            if field not in brief_data:
                return None, f"OpenAI response missing required field: {field}"
        
        # Ensure summary is a string (convert list to bullet points if needed)
        if isinstance(brief_data['summary'], list):
            brief_data['summary'] = '\n'.join([f"• {item}" if not item.startswith('•') else item for item in brief_data['summary']])
        elif not isinstance(brief_data['summary'], str):
            brief_data['summary'] = str(brief_data['summary'])
        
        # Ensure bullet points are properly formatted
        if '\n' in brief_data['summary']:
            lines = brief_data['summary'].split('\n')
            formatted_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    if not line.startswith('•') and not line.startswith('-') and not line.startswith('*'):
                        formatted_lines.append(f"• {line}")
                    else:
                        formatted_lines.append(line)
            brief_data['summary'] = '\n'.join(formatted_lines)
        else:
            # Single line summary, add bullet point
            if brief_data['summary'].strip() and not brief_data['summary'].strip().startswith('•'):
                brief_data['summary'] = f"• {brief_data['summary'].strip()}"
        
        return brief_data, None
        
    except json.JSONDecodeError as e:
        current_app.logger.error(f"Error parsing OpenAI JSON response: {str(e)}")
        return None, f"Error parsing AI response: {str(e)}"
    except RateLimitError as e:
        error_msg = str(e)
        current_app.logger.error(f"OpenAI rate limit error: {error_msg}")
        if "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
            return None, "OpenAI API quota exceeded. Please check your OpenAI account billing and quota limits at https://platform.openai.com/account/billing. You may need to upgrade your plan or wait for your quota to reset."
        return None, "OpenAI API rate limit exceeded. Please wait a moment and try again."
    except APIStatusError as e:
        error_msg = str(e)
        error_code = getattr(e, 'status_code', None) or getattr(e, 'code', None) or 0
        current_app.logger.error(f"OpenAI API status error (code {error_code}): {error_msg}")
        
        if error_code == 429 or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
            return None, "OpenAI API quota exceeded. Please check your OpenAI account billing and quota limits at https://platform.openai.com/account/billing. You may need to upgrade your plan or wait for your quota to reset."
        elif error_code == 401 or "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return None, "Invalid OpenAI API key. Please check your OPENAI_API_KEY environment variable."
        else:
            return None, f"OpenAI API error (code {error_code}): {error_msg}. Please check your OpenAI API configuration."
    except APIError as e:
        error_msg = str(e)
        error_code = getattr(e, 'status_code', None) or getattr(e, 'code', None)
        current_app.logger.error(f"OpenAI API error (code {error_code}): {error_msg}")
        
        if error_code == 429 or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
            return None, "OpenAI API quota exceeded. Please check your OpenAI account billing and quota limits at https://platform.openai.com/account/billing. You may need to upgrade your plan or wait for your quota to reset."
        elif error_code == 401 or "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return None, "Invalid OpenAI API key. Please check your OPENAI_API_KEY environment variable."
        elif error_code == 429:
            return None, "OpenAI API rate limit exceeded. Please wait a moment and try again."
        else:
            return None, f"OpenAI API error: {error_msg}. Please check your OpenAI API configuration."
    except APIConnectionError as e:
        current_app.logger.error(f"OpenAI connection error: {str(e)}")
        return None, "Failed to connect to OpenAI API. Please check your internet connection and try again."
    except APITimeoutError as e:
        current_app.logger.error(f"OpenAI timeout error: {str(e)}")
        return None, "OpenAI API request timed out. Please try again with a shorter text or check your connection."
    except Exception as e:
        error_str = str(e)
        current_app.logger.error(f"Unexpected error calling OpenAI API: {error_str}")
        
        # Fallback error message checking
        if "429" in error_str or "quota" in error_str.lower() or "insufficient_quota" in error_str.lower():
            return None, "OpenAI API quota exceeded. Please check your OpenAI account billing and quota limits at https://platform.openai.com/account/billing."
        elif "401" in error_str or "invalid_api_key" in error_str.lower():
            return None, "Invalid OpenAI API key. Please check your OPENAI_API_KEY environment variable."
        else:
            return None, f"Error generating research brief: {error_str}. Please check your OpenAI API configuration and try again."


def process_research_brief(source_text: str = None, pdf_data: bytes = None, pdf_filename: str = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Process either text or PDF to generate a research brief.
    
    Args:
        source_text: Direct text input
        pdf_data: PDF file data
        pdf_filename: Original PDF filename
        
    Returns:
        Tuple of (brief_data_dict, error_message)
    """
    try:
        # Extract text from PDF if provided
        if pdf_data:
            extracted_text, error = extract_text_from_pdf(pdf_data)
            if error:
                return None, error
            source_text = extracted_text
        
        if not source_text or len(source_text.strip()) < 50:
            return None, "Source text is too short. Please provide at least 50 characters of text."
        
        # Generate brief using OpenAI
        brief_data, error = generate_research_brief(source_text)
        if error:
            return None, error
        
        # Add source text to the brief data for storage
        brief_data['source_text'] = source_text
        
        return brief_data, None
        
    except Exception as e:
        current_app.logger.error(f"Error processing research brief: {str(e)}")
        return None, f"Error processing research brief: {str(e)}"
