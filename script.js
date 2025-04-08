// DOM Elements
const customerInput = document.getElementById('customerInput');
const submitBtn = document.getElementById('submitBtn');
const regenerateBtn = document.getElementById('regenerateBtn');
const copyBtn = document.getElementById('copyBtn');
const chatMessages = document.getElementById('chatMessages');
const generatedResponse = document.getElementById('generatedResponse');
const companySelect = document.getElementById('companySelect');

// State
let currentCompany = companySelect.value;
let lastCustomerMessage = '';

// Event Listeners
companySelect.addEventListener('change', (e) => {
    currentCompany = e.target.value;
});

submitBtn.addEventListener('click', handleSubmit);
regenerateBtn.addEventListener('click', handleRegenerate);
copyBtn.addEventListener('click', handleCopy);

// Main Functions
async function handleSubmit() {
    const customerMessage = customerInput.value.trim();
    
    if (!customerMessage) {
        alert('Please enter a message');
        return;
    }

    // Disable submit button and show loading state
    setLoadingState(true);
    
    // Add customer message to chat
    addMessageToChat(customerMessage, 'customer');
    
    try {
        const response = await generateResponse(customerMessage, currentCompany);
        
        // Add bot message to chat
        addMessageToChat(response, 'bot');
        
        // Display in response box
        generatedResponse.textContent = response;
        
        // Enable action buttons
        regenerateBtn.disabled = false;
        copyBtn.disabled = false;
        
        // Store last message for regeneration
        lastCustomerMessage = customerMessage;
        
        // Clear input
        customerInput.value = '';
        
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to generate response. Please try again.');
    }
    
    // Reset loading state
    setLoadingState(false);
}

async function handleRegenerate() {
    if (!lastCustomerMessage) return;
    
    setLoadingState(true);
    
    try {
        const response = await generateResponse(lastCustomerMessage, currentCompany);
        generatedResponse.textContent = response;
        
        // Update last bot message in chat
        const messages = chatMessages.getElementsByClassName('bot-message');
        if (messages.length > 0) {
            messages[messages.length - 1].textContent = response;
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to regenerate response. Please try again.');
    }
    
    setLoadingState(false);
}

async function handleCopy() {
    const response = generatedResponse.textContent;
    
    try {
        await navigator.clipboard.writeText(response);
        
        // Visual feedback
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyBtn.textContent = originalText;
        }, 2000);
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to copy to clipboard');
    }
}

// Helper Functions
function addMessageToChat(message, type) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${type}-message`);
    messageDiv.textContent = message;
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setLoadingState(isLoading) {
    submitBtn.disabled = isLoading;
    regenerateBtn.disabled = isLoading;
    copyBtn.disabled = isLoading;
    submitBtn.textContent = isLoading ? 'Generating...' : 'Generate Response';
}

// API call to Flask backend
async function generateResponse(message, company) {
    try {
        const response = await fetch('http://localhost:5000/api/generate-response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                company: company
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Display similar tweets
        displaySimilarTweets(data.similar_tweets);
        
        return data.response;
    } catch (error) {
        console.error('Error calling API:', error);
        throw error;
    }
}

// Add function to display similar tweets
function displaySimilarTweets(tweets) {
    const container = document.getElementById('similarTweets');
    container.innerHTML = ''; // Clear existing tweets
    
    tweets.forEach(tweet => {
        const tweetElement = document.createElement('div');
        tweetElement.className = 'similar-tweet';
        
        const similarity = (tweet.similarity * 100).toFixed(1);
        
        tweetElement.innerHTML = `
            <div class="similar-tweet-header">
                <span>${tweet.company}</span>
                <span class="similarity-score">${similarity}% similar</span>
            </div>
            <div class="similar-tweet-content">
                <strong>Customer:</strong> ${tweet.customer_tweet}
            </div>
            <div class="similar-tweet-response">
                <strong>Agent:</strong> ${tweet.company_tweet}
            </div>
        `;
        
        container.appendChild(tweetElement);
    });
}

// Initial setup
customerInput.focus(); 