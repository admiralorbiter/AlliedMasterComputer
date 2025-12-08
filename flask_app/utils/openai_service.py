# flask_app/utils/openai_service.py

import os
import json
import re
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
    "summary": "A well-structured bullet-point summary organized into clear sections. The summary field MUST be a plain text string (NOT a JSON object or array). Format it exactly like this example:\\n\\nKey Findings:\\n• First finding here\\n• Second finding here\\n• Third finding here\\n\\nMain Points:\\n• First main point\\n• Second main point\\n• Third main point\\n\\nMethodology/Approach:\\n• Method description if applicable\\n\\nConclusions/Recommendations:\\n• First recommendation\\n• Second recommendation\\n\\nCRITICAL: The summary must be a single plain text string with section headers ending in colons, followed by bullet points (•) on separate lines. Do NOT use JSON objects, arrays, or nested structures for the summary. Do NOT use quotes around section headers or bullet points. Each bullet point must be on its own line starting with •. If a section is not applicable, omit it entirely."
}}

Text to analyze:
{text[:150000]}"""  # Limit to ~150k chars to leave room for prompt and response
        
        # Determine if model supports JSON mode
        # Models that support response_format json_object:
        # GPT-5 models: gpt-5.1, gpt-5, gpt-5-mini, gpt-5-nano, gpt-5-pro, gpt-5-codex variants
        # GPT-4.1 models: gpt-4.1, gpt-4.1-mini, gpt-4.1-nano
        # GPT-4o models: gpt-4o, gpt-4o-mini
        # GPT-4 turbo models: gpt-4-turbo-preview, gpt-4-0125-preview, dated versions
        # GPT-3.5: gpt-3.5-turbo-0125
        # Note: Older models like gpt-4-turbo (without date) may not support it
        model_lower = model.lower()
        json_mode_models = [
            # GPT-5 models
            'gpt-5.1', 'gpt-5', 'gpt-5-mini', 'gpt-5-nano', 'gpt-5-pro',
            'gpt-5.1-codex-max', 'gpt-5.1-codex', 'gpt-5-codex', 'gpt-5.1-codex-mini',
            'gpt-5.1-chat-latest', 'gpt-5-chat-latest',
            # GPT-4.1 models
            'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano',
            # GPT-4o models
            'gpt-4o', 'gpt-4o-mini',
            # GPT-4 turbo models
            'gpt-4-turbo-preview', 'gpt-4-0125-preview', 
            'gpt-4-turbo-2024-04-09', 'gpt-4-turbo-2024-08-06', 'gpt-4-turbo-2024-11-20',
            # GPT-3.5 models
            'gpt-3.5-turbo-0125'
        ]
        supports_json_mode = (
            any(model_lower.startswith(m.lower()) for m in json_mode_models) or
            'gpt-5' in model_lower or  # All GPT-5 models support JSON mode
            'gpt-4.1' in model_lower or  # All GPT-4.1 models support JSON mode
            'gpt-4o' in model_lower or
            ('gpt-4-turbo' in model_lower and '-' in model)  # Date-suffixed versions
        )
        
        # Determine if this is a GPT-5 model (uses max_completion_tokens instead of max_tokens)
        is_gpt5_model = 'gpt-5' in model_lower
        
        # Build API call parameters
        api_params = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a research assistant that creates structured research briefs from academic and professional texts. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3
        }
        
        # GPT-5 models use max_completion_tokens, others use max_tokens
        # Increase limit for GPT-5 models as they may need more tokens for complex responses
        if is_gpt5_model:
            api_params["max_completion_tokens"] = 4000  # Increased for GPT-5 models
        else:
            api_params["max_tokens"] = 2000
        
        # Only add response_format if model supports it
        if supports_json_mode:
            api_params["response_format"] = {"type": "json_object"}
        
        # Call OpenAI API with structured output
        # Handle parameter compatibility issues with automatic retry
        try:
            response = client.chat.completions.create(**api_params)
        except Exception as e:
            error_str = str(e)
            retry_needed = False
            
            # Check if error is about response_format not being supported
            if "response_format" in error_str.lower() and "not supported" in error_str.lower() and "response_format" in api_params:
                current_app.logger.warning(f"Model {model} does not support response_format, retrying without it")
                api_params.pop("response_format", None)
                retry_needed = True
            
            # Check if error is about max_tokens not being supported (GPT-5 models need max_completion_tokens)
            elif "max_tokens" in error_str.lower() and "not supported" in error_str.lower() and "max_completion_tokens" in error_str.lower():
                current_app.logger.warning(f"Model {model} requires max_completion_tokens instead of max_tokens, retrying with correct parameter")
                max_tokens_value = api_params.pop("max_tokens", 2000)
                api_params["max_completion_tokens"] = max_tokens_value
                retry_needed = True
            
            # Check if error is about max_completion_tokens not being supported (older models need max_tokens)
            elif "max_completion_tokens" in error_str.lower() and "not supported" in error_str.lower():
                current_app.logger.warning(f"Model {model} requires max_tokens instead of max_completion_tokens, retrying with correct parameter")
                max_completion_value = api_params.pop("max_completion_tokens", 2000)
                api_params["max_tokens"] = max_completion_value
                retry_needed = True
            
            if retry_needed:
                response = client.chat.completions.create(**api_params)
            else:
                # Re-raise if it's a different error
                raise
        
        # Parse the response
        if not response.choices or len(response.choices) == 0:
            current_app.logger.error(f"OpenAI API returned no choices. Model: {model}, Response: {response}")
            return None, "OpenAI API returned no response choices"
        
        choice = response.choices[0]
        message = choice.message
        finish_reason = getattr(choice, 'finish_reason', None)
        
        # Log finish reason for debugging
        if finish_reason:
            current_app.logger.info(f"OpenAI API finish_reason: {finish_reason} for model {model}")
        
        # Check if response was cut off
        if finish_reason == 'length':
            current_app.logger.warning(f"OpenAI API response was cut off due to token limit. Model: {model}")
            return None, "OpenAI API response was cut off due to token limit. The response may be incomplete. Try reducing the input text size or increasing max_completion_tokens."
        
        if finish_reason == 'content_filter':
            current_app.logger.warning(f"OpenAI API response was filtered. Model: {model}")
            return None, "OpenAI API response was filtered. Please try again with different content."
        
        if not message:
            current_app.logger.error(f"OpenAI API returned no message. Model: {model}, Choice: {choice}")
            return None, "OpenAI API returned no message in response"
        
        if not message.content:
            # Log more details about what we got
            current_app.logger.error(
                f"OpenAI API returned empty content. Model: {model}, "
                f"Finish reason: {finish_reason}, "
                f"Message object: {message}, "
                f"Response object keys: {dir(response)}"
            )
            return None, f"OpenAI API returned empty response content (finish_reason: {finish_reason}). This may indicate the model stopped generating. Please try again."
        
        response_text = message.content.strip()
        if not response_text:
            current_app.logger.error(f"OpenAI API returned empty response text after strip. Model: {model}, Original content: {repr(message.content)}")
            return None, "OpenAI API returned empty response text"
        
        try:
            brief_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            # Log the full response for debugging (truncated to avoid log spam)
            current_app.logger.error(
                f"Failed to parse OpenAI response as JSON. "
                f"Model: {model}, Response length: {len(response_text)}, "
                f"First 500 chars: {response_text[:500]}, Error: {str(e)}"
            )
            return None, f"OpenAI API returned invalid JSON. The model may not have returned properly formatted JSON. Please try again or use a different model."
        
        # Validate required fields
        required_fields = ['title', 'citation', 'summary']
        for field in required_fields:
            if field not in brief_data:
                return None, f"OpenAI response missing required field: {field}"
        
        # Ensure summary is a string (handle dict, list, or string formats)
        if isinstance(brief_data['summary'], dict):
            # Convert dictionary structure to formatted text
            formatted_sections = []
            section_order = ['Key Findings', 'Main Points', 'Methodology/Approach', 'Methodology', 'Approach', 
                           'Conclusions/Recommendations', 'Conclusions', 'Recommendations']
            
            # Process sections in order
            for section_name in section_order:
                if section_name in brief_data['summary']:
                    section_content = brief_data['summary'][section_name]
                    formatted_sections.append(f"{section_name}:")
                    
                    # Handle list of items
                    if isinstance(section_content, list):
                        for item in section_content:
                            item_str = str(item).strip()
                            # Remove quotes if present
                            item_str = re.sub(r"^['\"]|['\"]$", '', item_str)
                            formatted_sections.append(f"• {item_str}")
                    elif isinstance(section_content, str):
                        # Split by newlines or bullets if it's a multi-line string
                        for line in section_content.split('\n'):
                            line = line.strip()
                            if line:
                                line = re.sub(r"^['\"]|['\"]$", '', line)
                                if not line.startswith('•'):
                                    formatted_sections.append(f"• {line}")
                                else:
                                    formatted_sections.append(line)
                    
                    # Don't add blank line - spacing will be handled by CSS margins
            
            # Also check for any other keys not in our standard list
            for key, value in brief_data['summary'].items():
                if key not in section_order:
                    formatted_sections.append(f"{key}:")
                    if isinstance(value, list):
                        for item in value:
                            item_str = str(item).strip()
                            item_str = re.sub(r"^['\"]|['\"]$", '', item_str)
                            formatted_sections.append(f"• {item_str}")
                    else:
                        value_str = str(value).strip()
                        value_str = re.sub(r"^['\"]|['\"]$", '', value_str)
                        formatted_sections.append(f"• {value_str}")
                    # Don't add blank line - spacing will be handled by CSS
            
            brief_data['summary'] = '\n'.join(formatted_sections).strip()
        elif isinstance(brief_data['summary'], list):
            brief_data['summary'] = '\n'.join([f"• {item}" if not item.startswith('•') else item for item in brief_data['summary']])
        elif not isinstance(brief_data['summary'], str):
            brief_data['summary'] = str(brief_data['summary'])
        
        # Format the summary with proper section headers and bullet points
        summary_text = brief_data['summary']
        
        # Clean up any JSON-like formatting artifacts
        # Remove quotes around section headers and bullet points
        # Remove quotes around section headers (e.g., 'Key Findings': -> Key Findings:)
        summary_text = re.sub(r"'([^']+)':", r'\1:', summary_text)
        # Remove quotes around bullet points
        summary_text = re.sub(r"'\s*•\s*([^']+)'", r'• \1', summary_text)
        summary_text = re.sub(r"'\s*-\s*([^']+)'", r'• \1', summary_text)
        # Remove leading/trailing quotes from lines
        summary_text = re.sub(r"^'|'$", '', summary_text, flags=re.MULTILINE)
        
        if '\n' in summary_text:
            lines = summary_text.split('\n')
            formatted_lines = []
            for line in lines:
                original_line = line
                line = line.strip()
                
                if not line:
                    formatted_lines.append('')  # Preserve blank lines for spacing
                    continue
                
                # Check if this is a section header (ends with colon or matches section names)
                section_headers = ['Key Findings', 'Main Points', 'Methodology', 'Approach', 
                                 'Conclusions', 'Recommendations', 'Methodology/Approach', 
                                 'Conclusions/Recommendations']
                is_section_header = False
                clean_header = None
                
                for header in section_headers:
                    # Check various formats: "Key Findings:", "'Key Findings':", etc.
                    if (line.startswith(header) or line.startswith(f"'{header}'") or 
                        line.startswith(f'"{header}"')):
                        # Extract just the header name
                        clean_header = header
                        is_section_header = True
                        break
                
                if is_section_header:
                    # Format as section header
                    formatted_lines.append(f"{clean_header}:")
                else:
                    # Format as bullet point
                    # Remove any JSON formatting artifacts
                    line = re.sub(r"^['\"]|['\"]$", '', line)  # Remove surrounding quotes
                    line = re.sub(r"^\s*['\"]\s*•\s*|^\s*•\s*['\"]", '• ', line)  # Clean bullet points
                    line = line.strip()
                    
                    # Ensure it starts with a bullet point
                    if not line.startswith('•') and not line.startswith('-') and not line.startswith('*'):
                        # Remove any leading asterisks or other markers
                        line = re.sub(r'^[\*\-\•\s]+', '', line)
                        formatted_lines.append(f"• {line}")
                    else:
                        # Clean up existing bullet points
                        line = re.sub(r'^[\*\-\•\s]+', '• ', line)
                        formatted_lines.append(line)
            
            # Join lines and clean up excessive blank lines
            brief_data['summary'] = '\n'.join(formatted_lines)
            # Remove more than 1 consecutive blank line (keep only single blank lines)
            brief_data['summary'] = re.sub(r'\n{2,}', '\n', brief_data['summary'])
            brief_data['summary'] = brief_data['summary'].strip()
        else:
            # Single line summary, add bullet point
            summary_text = summary_text.strip()
            summary_text = re.sub(r"^['\"]|['\"]$", '', summary_text)  # Remove quotes
            if summary_text and not summary_text.startswith('•'):
                brief_data['summary'] = f"• {summary_text}"
            else:
                brief_data['summary'] = summary_text
        
        # Add model name to the response
        brief_data['model_name'] = model
        
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
        
        # Validate brief_data was returned
        if not brief_data:
            return None, "OpenAI API returned no data. Please try again."
        
        # Add source text to the brief data for storage
        brief_data['source_text'] = source_text
        
        return brief_data, None
        
    except Exception as e:
        current_app.logger.error(f"Error processing research brief: {str(e)}")
        return None, f"Error processing research brief: {str(e)}"
