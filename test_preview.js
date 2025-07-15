function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

function testPreviewGeneration() {
    console.log('Testing preview generation...');
    
    const csrfToken = getCsrfToken();
    console.log('CSRF Token:', csrfToken);
    
    if (!csrfToken) {
        console.error('CSRF token not found!');
        return;
    }
    
    fetch('/3d/12/preview', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': csrfToken
        },
        body: JSON.stringify({
            render_type: '2d'
        })
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Run the test
testPreviewGeneration();
