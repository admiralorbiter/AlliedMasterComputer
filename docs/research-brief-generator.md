# Research Brief Generator

## Overview

The Research Brief Generator is an AI-powered feature that automatically creates structured research briefs from PDF documents or text input. Using OpenAI's API, it extracts key information, generates citations, and creates bullet-point summaries of research materials.

## Features

- **PDF Upload**: Upload PDF files (up to 25MB) and extract text automatically
- **Text Input**: Paste or type source text directly
- **AI-Powered Analysis**: Uses OpenAI to generate structured briefs with:
  - Descriptive titles
  - Properly formatted citations
  - Well-structured summaries organized into clear sections (Key Findings, Main Points, Methodology, Conclusions/Recommendations)
- **Database Storage**: All briefs are stored securely in the database
- **User-Specific**: Each user can only access their own research briefs
- **Edit & Manage**: Edit, view, and delete your research briefs
- **PDF Download**: Download original PDF files for any brief created from PDFs

## Getting Started

### Prerequisites

1. **OpenAI API Key**: You need an active OpenAI API key with available quota
   - Sign up at https://platform.openai.com/
   - Generate an API key from your account settings
   - Ensure you have sufficient quota/credits

2. **Environment Configuration**:
   ```bash
   # In your .env file or environment variables
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-4-turbo  # Optional, defaults to 'gpt-4-turbo'
   ```

### Accessing the Feature

1. Log in to your account
2. Click "Research Briefs" in the navigation menu
3. Click "Create New Brief" to start

## Usage Guide

### Creating a Research Brief from PDF

1. Navigate to the Research Briefs page
2. Click "Create New Brief"
3. Select "Upload PDF" as the input type
4. Choose a PDF file (maximum 25MB)
5. Click "Generate Brief"
6. Wait for processing (this may take a few moments)
7. Review and edit the generated brief if needed

**Note**: The PDF text extraction uses `pdfplumber` library, which works with most PDF formats. Some PDFs with complex layouts or scanned images may have limited text extraction.

### Creating a Research Brief from Text

1. Navigate to the Research Briefs page
2. Click "Create New Brief"
3. Select "Enter Text" as the input type
4. Paste or type your source text (minimum 50 characters)
5. Click "Generate Brief"
6. Wait for processing
7. Review and edit the generated brief if needed

### Viewing Your Briefs

- All your research briefs are listed on the main Research Briefs page
- Click on any brief title to view the full details
- Briefs are paginated (20 per page) and sorted by creation date (newest first)

### Editing a Brief

1. Open the brief you want to edit
2. Click the "Edit" button
3. Modify the title, citation, or summary
4. Click "Update Brief" to save changes

**Note**: You can only edit your own briefs. The source text and PDF data cannot be edited after creation.

### Downloading PDFs

If a brief was created from a PDF upload:
1. Open the brief
2. Click "Download PDF" to retrieve the original PDF file

### Deleting a Brief

1. Open the brief you want to delete
2. Click "Delete Brief" and confirm
3. **Warning**: This action cannot be undone

## How It Works

### Technical Flow

1. **Input Processing**:
   - PDF: Text is extracted using `pdfplumber` library
   - Text: Direct input is used as-is

2. **AI Processing**:
   - Extracted/input text is sent to OpenAI API
   - Uses structured output (JSON mode) for consistent formatting
   - Generates title, citation, and structured summary with organized sections:
     - Key Findings
     - Main Points
     - Methodology/Approach (if applicable)
     - Conclusions/Recommendations (if applicable)

3. **Storage**:
   - All data is stored in the `research_briefs` database table
   - PDFs are stored as binary data in the database
   - Source text is preserved for reference (extracted text for PDFs, original text for text input)
   - For PDF-based briefs, the source text is stored but not displayed in the view (since the original PDF is available for download)

### Database Schema

The `research_briefs` table includes:
- `id`: Primary key
- `user_id`: Foreign key to users table
- `title`: Generated or edited title
- `citation`: Generated or edited citation
- `summary`: Bullet-point summary
- `source_text`: Original extracted/input text
- `pdf_filename`: Original PDF filename (if applicable)
- `pdf_data`: Binary PDF data (if applicable)
- `source_type`: Either 'pdf' or 'text'
- `created_at`: Timestamp
- `updated_at`: Timestamp

## Configuration

### OpenAI Model Selection

You can specify which OpenAI model to use:

```bash
# In .env file
OPENAI_MODEL=gpt-4-turbo        # Default, recommended
OPENAI_MODEL=gpt-4               # Alternative
OPENAI_MODEL=gpt-3.5-turbo      # Faster, lower cost
```

**Recommendation**: `gpt-4-turbo` provides the best balance of quality and cost for research brief generation.

### File Size Limits

- Maximum PDF file size: **25 MB**
- This limit is enforced at both the form validation and Flask configuration level
- For larger documents, consider splitting them or using text input with excerpts

### Text Length Limits

- Minimum text length: **50 characters**
- Maximum text sent to OpenAI: **~150,000 characters** (automatically truncated if longer)
- Very long documents may need chunking (future enhancement)

## Error Handling

The system provides clear error messages for common issues:

### Quota Exceeded
**Error**: "OpenAI API quota exceeded"
**Solution**: 
- Check your OpenAI account billing at https://platform.openai.com/account/billing
- Upgrade your plan or wait for quota reset
- Verify you have available credits

### Invalid API Key
**Error**: "Invalid OpenAI API key"
**Solution**:
- Verify your `OPENAI_API_KEY` environment variable is set correctly
- Check that the key is active in your OpenAI account
- Ensure there are no extra spaces or quotes in the key

### Rate Limit Exceeded
**Error**: "OpenAI API rate limit exceeded"
**Solution**:
- Wait a few moments and try again
- Consider using a model with higher rate limits
- Check your OpenAI account tier limits

### PDF Extraction Issues
**Error**: "PDF appears to be empty or contains no extractable text"
**Solution**:
- The PDF may be image-based (scanned document)
- Try using OCR software first, then paste the text
- Verify the PDF is not corrupted
- Some PDFs with complex layouts may have limited extraction

## Best Practices

### For Best Results

1. **Quality Input**: 
   - Use well-formatted PDFs with extractable text
   - Provide complete, coherent text passages
   - Include context and full sentences

2. **Citation Accuracy**:
   - Review and edit generated citations
   - Add missing information (dates, page numbers, etc.)
   - Verify citation format matches your requirements

3. **Summary Review**:
   - AI-generated summaries are structured with clear sections for easy reading
   - Summaries include: Key Findings, Main Points, Methodology (if applicable), and Conclusions/Recommendations
   - Edit to emphasize important points or adjust the structure as needed
   - Sections that aren't applicable will be omitted by the AI

4. **File Management**:
   - Use descriptive titles for easy searching
   - Delete briefs you no longer need
   - Download and backup important PDFs

### Performance Tips

- **Shorter Texts**: Process faster and use fewer tokens
- **Focused Content**: Extract relevant sections rather than entire documents
- **Batch Processing**: Create multiple briefs for different sections of large documents

## Security & Privacy

- **User Isolation**: Users can only access their own research briefs
- **No Admin Override**: Even administrators cannot access other users' briefs
- **Secure Storage**: All data is stored in the database with proper access controls
- **API Security**: OpenAI API keys should be kept secure and never exposed in client-side code

## Troubleshooting

### Brief Generation Takes Too Long

- Check your internet connection
- Verify OpenAI API status at https://status.openai.com/
- Large PDFs or long texts take more time to process
- Consider using shorter text excerpts

### Generated Brief Quality Issues

- Try a different OpenAI model (e.g., `gpt-4` instead of `gpt-4-turbo`)
- Provide more context in your source text
- Edit the generated brief to improve it
- Break large documents into smaller, focused sections

### Database Issues

If you encounter database errors:
- Ensure the `research_briefs` table exists (run migrations if needed)
- Check database connection settings
- Verify user permissions

## API Integration Details

### OpenAI API Call Structure

The system uses OpenAI's Chat Completions API with:
- **Model**: Configurable (default: gpt-4-turbo)
- **Response Format**: JSON mode for structured output
- **Temperature**: 0.3 (for consistent, focused responses)
- **Max Tokens**: 2000 (for summary generation)

### Prompt Engineering

The system uses a carefully crafted prompt that:
- Requests structured JSON output
- Specifies format requirements for title, citation, and summary
- Instructs the AI to create comprehensive but concise summaries
- Ensures bullet-point formatting

## Future Enhancements

Potential improvements for future versions:
- Batch processing of multiple PDFs
- Custom citation format templates
- Export briefs to various formats (PDF, DOCX, Markdown)
- Search and filtering capabilities
- Tagging and categorization
- Integration with reference management tools
- OCR support for scanned PDFs
- Multi-language support
- Collaborative brief sharing (optional)

## Support

For issues or questions:
1. Check this documentation
2. Review error messages for specific guidance
3. Check OpenAI API status and your account status
4. Review application logs for detailed error information

## Related Documentation

- [Main README](../README.md) - General application setup
- [Database Models](../flask_app/models/research_brief.py) - Technical model details
- [OpenAI Service](../flask_app/utils/openai_service.py) - API integration code
