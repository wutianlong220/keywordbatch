# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a keyword processing tool project based on the Chrome extension MVP in the `keywords_tools` reference folder. The project will be initialized to create a modern keyword batch processing application with translation, Kdroi calculation, and multi-platform link generation capabilities.

## Reference Project Structure

The `keywords_tools/` folder contains a working Chrome extension MVP that demonstrates:
- **File Processing**: XLSX file batch processing with drag-and-drop support
- **AI Integration**: DeepSeek API integration for keyword translation
- **Data Analysis**: Kdroi calculation (Volume × CPC ÷ Keyword Difficulty)
- **Link Generation**: Google Search, Google Trends, and Ahrefs query links
- **UI Components**: Popup interface with progress tracking

## Key Reference Files

- `keywords_tools/popup.js:1` - Main keyword processing logic and API integration
- `keywords_tools/popup.html` - UI structure and layout
- `keywords_tools/manifest.json` - Chrome extension configuration
- `keywords_tools/background.js` - Background service worker
- `keywords_tools/README.md` - Complete feature documentation

## Technology Stack (Based on Reference)

- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript (ES6+)
- **File Processing**: SheetJS (XLSX library)
- **API Integration**: DeepSeek Chat Completions API
- **Data Storage**: Chrome Storage API (for extension version)

## Project Initialization Commands

Since this is a new project, common development commands will be:

```bash
# Initialize new project (choose appropriate template)
npm init -y
# or for other frameworks:
# python -m venv venv
# cargo init
# etc.

# Install dependencies based on chosen stack
npm install [dependencies]
# or pip install -r requirements.txt
# etc.

# Development server
npm run dev
# or python main.py
# etc.

# Build for production
npm run build
# or equivalent
```

## Architecture Notes

The reference implementation follows these patterns:
- **Modular Design**: Separate classes for different functionalities (KeywordProcessor)
- **Event-Driven**: Extensive use of event listeners for user interactions
- **API Integration**: Configurable API endpoints and authentication
- **File Processing**: Streaming file processing for large datasets
- **Progress Tracking**: Real-time progress updates and error handling
- **Data Validation**: Input validation and error recovery

## Security Considerations

Based on the reference project:
- **Local Processing**: All data processing happens locally
- **API Security**: API keys stored locally, not in code
- **File Security**: No file uploads to external servers
- **User Privacy**: All data remains on user's device

## Development Patterns

When working with this codebase:
1. **Reference the keywords_tools folder** for implementation details
2. **Follow the modular class structure** from the reference
3. **Implement proper error handling** and user feedback
4. **Use async/await patterns** for API calls and file processing
5. **Include progress tracking** for long-running operations
6. **Maintain data validation** throughout the processing pipeline