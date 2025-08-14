// BidLord JavaScript
document.addEventListener('DOMContentLoaded', function () {
    console.log('BidLord application loaded');

    // Check API health
    checkApiHealth();

    // Add click handlers for API docs
    const apiLinks = document.querySelectorAll('.api-docs-link');
    apiLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            console.log('Navigating to API documentation');
        });
    });
});

function checkApiHealth() {
    fetch('/api/v1/accounts/health/')
        .then(response => response.json())
        .then(data => {
            console.log('API Health:', data);
            updateHealthStatus(true);
        })
        .catch(error => {
            console.error('API Health Check Failed:', error);
            updateHealthStatus(false);
        });
}

function updateHealthStatus(isHealthy) {
    const statusIndicators = document.querySelectorAll('.status-indicator');
    statusIndicators.forEach(indicator => {
        indicator.className = isHealthy ?
            'status-indicator status-online' :
            'status-indicator status-offline';
    });
}

// Utility functions for future use
const BidLord = {
    api: {
        baseUrl: '/api/v1',

        async request(endpoint, options = {}) {
            const url = `${this.baseUrl}${endpoint}`;
            const config = {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            };

            const response = await fetch(url, config);
            return response.json();
        },

        async get(endpoint) {
            return this.request(endpoint);
        },

        async post(endpoint, data) {
            return this.request(endpoint, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }
    },

    utils: {
        formatCurrency(amount) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(amount);
        },

        formatDate(date) {
            return new Intl.DateTimeFormat('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(new Date(date));
        }
    }
};

// Make BidLord available globally
window.BidLord = BidLord;
