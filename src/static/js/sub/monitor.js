// monitor.js

const socket = io();

document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light-mode'; // Default to light-mode
    document.body.classList.add(savedTheme);

    const themeButton = document.querySelector('.theme-toggle-button');
    if (savedTheme === 'dark-mode') {
        themeButton.classList.remove('light-mode');
        themeButton.classList.add('dark-mode');
        themeButton.innerText = 'D';
    } else {
        themeButton.classList.remove('dark-mode');
        themeButton.classList.add('light-mode');
        themeButton.innerText = 'L';
    }
});

function startMonitoring() {
    // Emit an event to start monitoring
    socket.emit('start_monitoring');

    // Listen for the 'camera_frame' event
    socket.on('camera_frame', function(data) {
        const sessionId = data.session_id;
        let streamContainer = document.getElementById(`stream_container_${sessionId}`);

        // Ensure the container element exists
        const container = document.getElementById('camera_streams_container');
        if (!container) {
            console.error('Container element with id "camera_streams_container" not found.');
            return;
        }

        // If the stream container does not exist, create it
        if (!streamContainer) {
            console.log(`Creating stream container with session ID: ${sessionId}`);

            streamContainer = document.createElement('div');
            streamContainer.id = `stream_container_${sessionId}`;
            streamContainer.className = 'stream-container';

            // Create the img element
            const imgElement = document.createElement('img');
            imgElement.id = `camera_stream_${sessionId}`;
            imgElement.width = 640;
            imgElement.height = 360;

            // Create the label for the session ID
            const idLabel = document.createElement('p');
            idLabel.className = 'session-id';
            idLabel.innerText = `${sessionId}`;

            // Append img and label to the stream container
            streamContainer.appendChild(imgElement);
            streamContainer.appendChild(idLabel);

            // Append the stream container to the main container
            container.appendChild(streamContainer);
        }

        // Update the image source with the new frame
        const imgElement = document.getElementById(`camera_stream_${sessionId}`);
        imgElement.src = `data:image/jpeg;base64,${data.frame}`;
    });

    // Listen for the 'remove_camera_stream' event
    socket.on('remove_camera_stream', function(data) {
        console.log('remove_camera_stream event received:', data); // Log the event data
        const streamContainer = document.getElementById(`stream_container_${data.session_id}`);
        if (streamContainer) {
            console.log(`Removing stream container for session ID: ${data.session_id}`);
            streamContainer.remove();
        } else {
            console.warn(`Stream container with id "stream_container_${data.session_id}" not found.`);
        }
    });
}

window.onload = function() {
    startMonitoring();
};
