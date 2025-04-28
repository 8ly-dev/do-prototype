/**
 * Flowstate Chat Interface
 *
 * This module provides a reusable chat interface for Flowstate.
 * It handles WebSocket connections, message display, and user interactions.
 */

// Main chat interface class
class FlowstateChat {
    constructor(options = {}) {
        // Default options
        this.options = {
            // WebSocket path - can be overridden for different pages
            websocketPath: '/ws',

            // Placeholders for the input field
            placeholders: [
                "Let's do...",
                "I want to...",
                "Remind me to...",
                "Schedule...",
                "Start working on...",
                "Don't forget to..."
            ],

            // Interval for changing placeholders
            placeholderInterval: 30000, // 30 seconds

            // Whether to fade out old messages when a new one is added
            fadeOutOldMessages: false,

            // Complex message handling is now used for all pages

            // Whether to support suggested questions/actions
            supportSuggestedQuestions: false,

            // Whether to support tool messages
            supportToolMessages: false,

            // Override with any provided options
            ...options
        };

        // DOM elements
        this.elements = {
            chatForm: document.getElementById('chat-form'),
            chatInput: document.getElementById('chat-input'),
            chatMessages: document.getElementById('chat-messages'),
            loadingIndicator: document.getElementById('loading-indicator'),
            suggestedQuestions: document.getElementById('suggested-questions'),
            toolMessagesContainer: document.getElementById('tool-messages-container')
        };

        // Initialize
        this.init();
    }

    init() {
        // Set up event listeners
        this.setupEventListeners();

        // Set initial placeholder
        this.updatePlaceholder();

        // Change placeholder periodically
        setInterval(() => this.updatePlaceholder(), this.options.placeholderInterval);

        // Create WebSocket connection
        this.connectWebSocket();
    }

    setupEventListeners() {
        // Form submission
        this.elements.chatForm.addEventListener('submit', (event) => this.handleFormSubmit(event));

        // Global keyboard events for focusing input
        document.addEventListener('keydown', (event) => this.handleKeydown(event));

        // Task completion buttons (if they exist)
        this.setupTaskCompletionButtons();
    }

    setupTaskCompletionButtons() {
        // Find all task completion buttons
        const completeTaskButtons = document.querySelectorAll('.complete-task-button');

        if (completeTaskButtons.length > 0) {
            completeTaskButtons.forEach(button => {
                button.addEventListener('click', (event) => this.handleTaskCompletion(event));

                // Add keyboard support for task completion
                button.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        button.click();
                    }
                });
            });
        }
    }

    handleTaskCompletion(event) {
        const button = event.currentTarget;
        const taskId = button.getAttribute('data-task-id');

        // Send task completion to server
        this.socket.send(JSON.stringify({
            type: 'complete_task',
            task_id: taskId,
            timestamp: new Date().toISOString()
        }));

        // Visual feedback
        button.classList.add('bg-green-500');
        button.classList.remove('bg-indigo-600');

        // Handle different behaviors based on context
        const taskCard = button.closest('.task-card');

        if (taskCard) {
            // Project page behavior - remove the task card after animation
            setTimeout(() => {
                taskCard.style.opacity = '0';
                taskCard.style.height = '0';
                taskCard.style.margin = '0';
                taskCard.style.padding = '0';
                taskCard.style.overflow = 'hidden';
                taskCard.style.transition = 'all 0.5s ease';

                setTimeout(() => {
                    if (taskCard.parentNode) {
                        taskCard.parentNode.removeChild(taskCard);
                    }
                }, 500);
            }, 1000);
        } else {
            // Dashboard behavior - refresh the page after animation
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    }

    handleKeydown(event) {
        // Check if the key pressed is a printable character and not a modifier key
        const isPrintableKey = event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey;

        // If the chat input is not already focused and a printable key is pressed
        if (document.activeElement !== this.elements.chatInput && isPrintableKey) {
            // Focus the input field
            this.elements.chatInput.focus();

            // Add the pressed key to the input field
            this.elements.chatInput.value += event.key;

            // Prevent default to avoid double input
            event.preventDefault();

            // Set cursor position to the end of the input
            const length = this.elements.chatInput.value.length;
            this.elements.chatInput.setSelectionRange(length, length);
        }
    }

    updatePlaceholder() {
        const { placeholders } = this.options;
        this.elements.chatInput.placeholder = placeholders[Math.floor(Math.random() * placeholders.length)];
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        let path = this.options.websocketPath;

        // Check if we're on a project page and need to include the project ID
        const projectId = document.body.getAttribute('data-project-id');
        if (projectId && path === '/ws') {
            path = `/ws/${projectId}`;
        }

        this.socket = new WebSocket(`${protocol}//${window.location.host}${path}`);

        // Connection opened
        this.socket.addEventListener('open', () => {
            console.log('Connected to WebSocket server');
        });

        // Listen for messages
        this.socket.addEventListener('message', (event) => this.handleSocketMessage(event));

        // Connection closed
        this.socket.addEventListener('close', () => {
            console.log('Disconnected from WebSocket server');
            this.hideLoadingIndicator();
            if (this.options.supportToolMessages) {
                this.fadeOutAllToolMessages();
            }
            this.addMessage('Connection closed. Please refresh the page to reconnect.', 'system');
        });

        // Connection error
        this.socket.addEventListener('error', (event) => {
            console.error('WebSocket error:', event);
            this.hideLoadingIndicator();
            if (this.options.supportToolMessages) {
                this.fadeOutAllToolMessages();
            }
            this.addMessage('Error connecting to server.', 'system');
        });
    }

    handleSocketMessage(event) {
        // Complex message handling for all pages
        try {
            const data = JSON.parse(event.data);

            switch (data.kind) {
                case 'command':
                    if (data.command === 'typing') {
                        this.showLoadingIndicator();
                    } else if (data.command === 'login_success') {
                        // Handle login success
                        this.hideLoadingIndicator();

                        // Set the session token as a cookie
                        if (data.token) {
                            document.cookie = `SESSION_TOKEN=${data.token}; path=/; max-age=2592000`; // 30 days
                        }

                        window.login_success = true;
                    }
                    break;
                case 'reply':
                    this.hideLoadingIndicator();
                    this.addMessage(data.reply, 'system');
                    if (this.options.supportToolMessages) {
                        this.fadeOutAllToolMessages();
                    }
                    if(window.login_success) {
                        setTimeout(() => {
                            window.location.href = '/';
                        }, 5000);
                    }
                    break;
                case 'action':
                    if (this.options.supportSuggestedQuestions) {
                        this.addActions(data.actions);
                    }
                    break;
                case 'using':
                    if (this.options.supportToolMessages) {
                        console.log("Using " + data.tool_message);
                        this.addToolMessage(data.tool_message);
                    }
                    break;
                default:
                    console.log(data);
                    console.warn(`Unknown message kind: ${data.kind}`);
            }
        } catch (error) {
            // Legacy format support - if parsing fails, treat it as a simple message
            console.warn('Message not in JSON format, treating as legacy format:', error);
            const message = event.data;

            if (message === "!!COMMAND: typing!!") {
                this.showLoadingIndicator();
            } else {
                this.hideLoadingIndicator();
                this.addMessage(message, 'system');
            }
        }
    }

    handleFormSubmit(event) {
        event.preventDefault();
        const message = this.elements.chatInput.value.trim();

        if (message) {
            // Show the user's message
            this.addMessage(message, 'user');

            // Send message to server using structured format
            this.socket.send(JSON.stringify({
                kind: 'prompt',
                prompt: message
            }));

            // Show loading indicator
            this.showLoadingIndicator();

            // Clear input
            this.elements.chatInput.value = '';
        }
    }

    sendSuggestedQuestion(question) {
        // Show the user's message
        this.addMessage(question, 'user');

        // Show loading indicator
        this.showLoadingIndicator();

        // Send message to server using structured format
        this.socket.send(JSON.stringify({
            kind: 'prompt',
            prompt: question
        }));
    }

    addActions(actions) {
        if (!this.options.supportSuggestedQuestions) {
            return;
        }

        // Create a new suggested questions container to be placed after the last message
        const suggestedQuestionsContainer = document.createElement('div');
        suggestedQuestionsContainer.id = 'suggested-questions-inline';
        suggestedQuestionsContainer.className = 'suggested-questions-inline';

        // Add the suggested questions to the container
        actions.forEach(action => {
            const questionLink = document.createElement('a');
            questionLink.href = '#';
            questionLink.textContent = action;
            questionLink.addEventListener('click', event => {
                let text = event.target.innerText;
                this.addMessage(text, 'user');
                this.showLoadingIndicator();
                this.socket.send(JSON.stringify({
                    kind: 'prompt',
                    prompt: text
                }));
                event.preventDefault();
                return false;
            });
            suggestedQuestionsContainer.appendChild(questionLink);
        });

        // Add the container after the last message
        const lastMessage = this.elements.chatMessages.lastElementChild;
        if (lastMessage) {
            lastMessage.after(suggestedQuestionsContainer);
        } else {
            this.elements.chatMessages.appendChild(suggestedQuestionsContainer);
        }

        // If we still have the old suggested questions element in the sidebar, hide it
        if (this.elements.suggestedQuestions) {
            this.elements.suggestedQuestions.classList.add('hide-suggestions');
        }
    }

    addMessage(message, type) {
        // Apply fade-out animation to existing messages if enabled
        if (this.options.fadeOutOldMessages) {
            const existingMessages = this.elements.chatMessages.querySelectorAll('.user-message, .system-message');
            existingMessages.forEach(msg => {
                msg.classList.add('message-fade-out');
            });

            // Remove old messages after animation completes
            setTimeout(() => {
                existingMessages.forEach(msg => {
                    if (msg.parentNode === this.elements.chatMessages) {
                        this.elements.chatMessages.removeChild(msg);
                    }
                });
            }, 1000); // Match animation duration
        }

        // Create new message element
        const messageElement = document.createElement('div');
        messageElement.classList.add(type === 'user' ? 'user-message' : 'system-message');
        messageElement.classList.add('message-fade-in', 'markdown-content');

        // Convert markdown to HTML using marked.js
        try {
            // Configure marked for security
            marked.setOptions({
                breaks: true,   // Convert line breaks to <br>
                gfm: true       // Enable GitHub Flavored Markdown
            });

            // Parse markdown to HTML
            const htmlContent = marked.parse(message);

            // Add content wrapper div for learn_more page
            if (this.options.useComplexMessageHandling) {
                messageElement.innerHTML = `<div class="content">${htmlContent}</div>`;
            } else {
                messageElement.innerHTML = htmlContent;
            }
        } catch (error) {
            console.error('Error parsing markdown:', error);
            // Fallback to plain text if markdown parsing fails
            messageElement.innerHTML = `<p>${message}</p>`;
        }

        // Add new message
        this.elements.chatMessages.appendChild(messageElement);
    }

    showLoadingIndicator() {
        this.elements.loadingIndicator.style.display = 'block';

        // Hide both inline and sidebar suggested questions when loading
        if (this.options.supportSuggestedQuestions) {
            // Hide sidebar suggested questions if they exist
            if (this.elements.suggestedQuestions) {
                this.elements.suggestedQuestions.classList.add('hide-suggestions');
            }

            // Hide inline suggested questions
            const inlineSuggestions = document.getElementById('suggested-questions-inline');
            if (inlineSuggestions) {
                inlineSuggestions.remove();
            }
        }
    }

    hideLoadingIndicator() {
        this.elements.loadingIndicator.style.display = 'none';
    }

    addToolMessage(message) {
        if (!this.options.supportToolMessages || !this.elements.toolMessagesContainer) {
            return;
        }

        // Make existing tool messages slide up and fade out
        this.fadeOutAllToolMessages();

        // Create new tool message element
        const toolMessageElement = document.createElement('div');
        const toolMessageTextElement = document.createElement('div');
        toolMessageElement.classList.add('tool-message');
        toolMessageElement.classList.add('tool-message-fade-in');
        toolMessageTextElement.classList.add('thinking');
        toolMessageTextElement.textContent = message;
        toolMessageElement.appendChild(toolMessageTextElement);

        // Add new tool message
        this.elements.toolMessagesContainer.appendChild(toolMessageElement);
    }

    fadeOutAllToolMessages() {
        if (!this.options.supportToolMessages || !this.elements.toolMessagesContainer) {
            return;
        }

        const toolMessages = this.elements.toolMessagesContainer.querySelectorAll('.tool-message');
        toolMessages.forEach(msg => {
            msg.classList.remove('tool-message-fade-in');
            msg.classList.add('tool-message-fade-out');
            // Remove after animation completes
            setTimeout(() => {
                if (msg.parentNode === this.elements.toolMessagesContainer) {
                    this.elements.toolMessagesContainer.removeChild(msg);
                }
            }, 500); // Match animation duration
        });
    }
}

// Helper function to fill the chat input with text (used by some pages)
function fillTextarea(linkElement) {
    document.getElementById("chat-input").value = linkElement.textContent || linkElement.innerText;
}

// Note: Chat is now initialized in the base template
// The auto-initialization below has been removed to prevent double connections