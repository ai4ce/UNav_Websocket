// monitor.js

const socket = io();

document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light-mode';
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
    socket.emit('start_monitoring');

    socket.on('camera_frame', function(data) {
        const sessionId = data.session_id;
        let streamContainer = document.getElementById(`stream_container_${sessionId}`);

        const container = document.getElementById('camera_streams_container');
        if (!container) {
            console.error('Container element with id "camera_streams_container" not found.');
            return;
        }

        if (!streamContainer) {
            console.log(`Creating stream container with session ID: ${sessionId}`);

            streamContainer = document.createElement('div');
            streamContainer.id = `stream_container_${sessionId}`;
            streamContainer.className = 'stream-container';

            const imgElement = document.createElement('img');
            imgElement.id = `camera_stream_${sessionId}`;
            imgElement.width = 640;
            imgElement.height = 360;

            const idLabel = document.createElement('p');
            idLabel.className = 'session-id';
            idLabel.innerText = `${sessionId}`;

            streamContainer.appendChild(imgElement);
            streamContainer.appendChild(idLabel);

            container.appendChild(streamContainer);

            streamContainer.addEventListener('click', () => {
                window.location.href = `/floorplan?session_id=${sessionId}`;
            });
        }

        const imgElement = document.getElementById(`camera_stream_${sessionId}`);
        imgElement.src = `data:image/jpeg;base64,${data.frame}`;
    });

    socket.on('remove_camera_stream', function(data) {
        console.log('remove_camera_stream event received:', data);
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
