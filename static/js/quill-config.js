/**
 * Quill Editor Configuration for Research Brief Summaries
 * Provides markdown shortcuts, smart lists, and paste formatting
 */

(function() {
    'use strict';

    // Quill configuration
    const quillConfig = {
        theme: 'snow',
        modules: {
            toolbar: [
                [{ 'header': [1, 2, 3, false] }],
                ['bold', 'italic'],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                ['link'],
                ['clean']
            ],
            clipboard: {
                matchVisual: false
            }
        },
        formats: ['header', 'bold', 'italic', 'list', 'bullet', 'link', 'blockquote']
    };

    /**
     * Initialize Quill editor for summary field
     * @param {string} editorId - ID of the editor container div
     * @param {string} hiddenInputId - ID of the hidden input field
     * @param {string} initialContent - Initial HTML content (optional)
     * @returns {Object} Quill instance
     */
    function initQuillEditor(editorId, hiddenInputId, initialContent) {
        const editorContainer = document.getElementById(editorId);
        const hiddenInput = document.getElementById(hiddenInputId);
        
        if (!editorContainer || !hiddenInput) {
            console.error('Quill editor container or hidden input not found');
            return null;
        }

        // Initialize Quill
        const quill = new Quill('#' + editorId, quillConfig);

        // Set initial content if provided
        if (initialContent && initialContent.trim()) {
            const trimmedContent = initialContent.trim();
            
            // Check if content is HTML (contains HTML tags)
            const isHTML = /<[a-z][\s\S]*>/i.test(trimmedContent);
            
            // Use a more direct approach: set HTML directly on the editor root
            // This is more reliable than clipboard conversion
            try {
                if (isHTML) {
                    // For HTML content, set it directly on the editor root
                    // Quill will parse and format it correctly
                    quill.root.innerHTML = trimmedContent;
                    // Update Quill's internal state
                    quill.update('silent');
                } else {
                    // Plain text - convert to HTML first (preserving line breaks)
                    const lines = trimmedContent.split('\n');
                    let htmlContent = '';
                    
                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i].trim();
                        if (line) {
                            htmlContent += `<p>${line}</p>`;
                        } else if (i < lines.length - 1) {
                            htmlContent += '<p><br></p>';
                        }
                    }
                    
                    if (!htmlContent) {
                        htmlContent = `<p>${trimmedContent}</p>`;
                    }
                    
                    quill.root.innerHTML = htmlContent;
                    quill.update('silent');
                }
                
                // Verify content was set and sync to hidden input
                setTimeout(function() {
                    const html = quill.root.innerHTML;
                    if (html && html !== '<p><br></p>' && html !== '<p></p>') {
                        hiddenInput.value = html;
                    }
                }, 10);
                
            } catch (error) {
                console.error('Error loading content into Quill:', error);
                // Fallback: try clipboard conversion method
                try {
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = isHTML ? trimmedContent : `<p>${trimmedContent}</p>`;
                    const delta = quill.clipboard.convert(tempDiv);
                    quill.setContents(delta, 'silent');
                    quill.update();
                } catch (fallbackError) {
                    console.error('All methods failed, using plain text:', fallbackError);
                    quill.setText(trimmedContent);
                }
            }
        }

        // Sync Quill content to hidden input on text change
        quill.on('text-change', function() {
            const html = quill.root.innerHTML;
            // Only update if content is not just empty paragraph
            if (html !== '<p><br></p>' && html !== '<p></p>') {
                hiddenInput.value = html;
            } else {
                hiddenInput.value = '';
            }
        });

        // Also sync on selection change (for paste events)
        quill.on('selection-change', function() {
            const html = quill.root.innerHTML;
            if (html !== '<p><br></p>' && html !== '<p></p>') {
                hiddenInput.value = html;
            } else {
                hiddenInput.value = '';
            }
        });

        // Markdown shortcuts handler
        setupMarkdownShortcuts(quill);

        // Smart list handler
        setupSmartLists(quill);

        // Paste formatting handler
        setupPasteFormatting(quill);

        // Ensure hidden input is updated before form submit
        const form = hiddenInput.closest('form');
        if (form) {
            form.addEventListener('submit', function() {
                const html = quill.root.innerHTML;
                if (html !== '<p><br></p>' && html !== '<p></p>') {
                    hiddenInput.value = html;
                } else {
                    hiddenInput.value = '';
                }
            });
        }

        return quill;
    }

    /**
     * Setup markdown shortcuts (e.g., # for heading, ** for bold)
     */
    function setupMarkdownShortcuts(quill) {
        quill.on('text-change', function(delta, oldDelta, source) {
            if (source !== 'user') return;

            const selection = quill.getSelection();
            if (!selection) return;

            const [line, offset] = quill.getLine(selection.index);
            const lineText = line.domNode.textContent || '';
            const lineStart = selection.index - offset;

            // Heading shortcuts (# ## ###)
            if (lineText.match(/^#{1,3}\s/)) {
                const match = lineText.match(/^(#{1,3})\s/);
                if (match) {
                    const level = match[1].length;
                    const textAfter = lineText.substring(match[0].length);
                    
                    quill.deleteText(lineStart, offset, 'user');
                    quill.insertText(lineStart, textAfter, 'user');
                    quill.formatLine(lineStart, textAfter.length, { header: level }, 'user');
                    quill.setSelection(lineStart + textAfter.length);
                    return;
                }
            }

            // Bold shortcut (**text**)
            const boldMatch = lineText.match(/\*\*([^*]+)\*\*/);
            if (boldMatch && offset > boldMatch.index + boldMatch[0].length - 1) {
                const start = lineStart + boldMatch.index;
                const end = start + boldMatch[0].length;
                const text = boldMatch[1];
                
                quill.deleteText(start, boldMatch[0].length, 'user');
                quill.insertText(start, text, { bold: true }, 'user');
                quill.setSelection(start + text.length);
                return;
            }

            // Italic shortcut (*text*)
            const italicMatch = lineText.match(/\*([^*]+)\*/);
            if (italicMatch && !lineText.match(/\*\*/) && offset > italicMatch.index + italicMatch[0].length - 1) {
                const start = lineStart + italicMatch.index;
                const end = start + italicMatch[0].length;
                const text = italicMatch[1];
                
                quill.deleteText(start, italicMatch[0].length, 'user');
                quill.insertText(start, text, { italic: true }, 'user');
                quill.setSelection(start + text.length);
                return;
            }
        });
    }

    /**
     * Setup smart list detection (auto-format when typing - or * at line start)
     * DISABLED: This was causing text duplication issues. Users should use the toolbar
     * or Quill's native list formatting instead.
     */
    function setupSmartLists(quill) {
        // Disabled to avoid interfering with Quill's native list behavior
        // Users can create lists using:
        // 1. The toolbar buttons
        // 2. Quill's native keyboard shortcuts
        // 3. Typing "- " and then using the toolbar to format
        
        // If you want to re-enable this, be very careful about:
        // - Not triggering multiple times
        // - Not interfering with Quill's native list formatting
        // - Properly handling edge cases
        return;
    }

    /**
     * Setup paste formatting to auto-detect structure
     */
    function setupPasteFormatting(quill) {
        quill.clipboard.addMatcher(Node.TEXT_NODE, function(node, delta) {
            const text = node.data;
            const Delta = Quill.import('delta');
            
            // Convert markdown-style headings
            if (text.match(/^#{1,3}\s/)) {
                const match = text.match(/^(#{1,3})\s(.+)/);
                if (match) {
                    const level = match[1].length;
                    const content = match[2];
                    return new Delta()
                        .insert(content, { header: level })
                        .insert('\n');
                }
            }

            // Convert markdown-style bold
            const boldRegex = /\*\*([^*]+)\*\*/g;
            if (boldRegex.test(text)) {
                let newDelta = new Delta();
                let lastIndex = 0;
                let match;
                
                boldRegex.lastIndex = 0; // Reset regex
                while ((match = boldRegex.exec(text)) !== null) {
                    if (match.index > lastIndex) {
                        newDelta.insert(text.substring(lastIndex, match.index));
                    }
                    newDelta.insert(match[1], { bold: true });
                    lastIndex = match.index + match[0].length;
                }
                
                if (lastIndex < text.length) {
                    newDelta.insert(text.substring(lastIndex));
                }
                
                return newDelta;
            }

            // Convert markdown-style lists
            const lines = text.split('\n');
            const newDelta = new Delta();
            
            lines.forEach((line, index) => {
                if (line.match(/^[-*]\s/)) {
                    const content = line.substring(2);
                    newDelta.insert(content, { list: 'bullet' });
                } else if (line.match(/^\d+\.\s/)) {
                    const content = line.substring(line.indexOf('.') + 2);
                    newDelta.insert(content, { list: 'ordered' });
                } else {
                    newDelta.insert(line);
                }
                
                if (index < lines.length - 1) {
                    newDelta.insert('\n');
                }
            });
            
            return newDelta;
        });
    }

    // Export for use in templates
    window.initQuillEditor = initQuillEditor;

})();
