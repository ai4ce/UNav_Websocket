const socket = io();

document.addEventListener('DOMContentLoaded', () => {
    // Check if the user has a saved theme preference
    const savedTheme = localStorage.getItem('theme');
    let theme;

    if (savedTheme) {
        theme = savedTheme;
    } else {
        // Automatically set theme based on system preference if no saved theme
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        theme = systemPrefersDark ? 'dark-mode' : 'light-mode';
    }

    document.body.classList.add(theme);

    const themeButton = document.querySelector('.theme-toggle-button');
    if (theme === 'dark-mode') {
        themeButton.classList.remove('light-mode');
        themeButton.classList.add('dark-mode');
        themeButton.innerText = 'D';
    } else {
        themeButton.classList.remove('dark-mode');
        themeButton.classList.add('light-mode');
        themeButton.innerText = 'L';
    }
});

let selectedImageBase64 = null;
let selectedDestination = null;
let currentPose = null;

socket.on('log', function(msg) {
    document.getElementById('server_output').innerHTML += `<p>${msg.data}</p>`;
    document.getElementById('server_output').scrollTop = document.getElementById('server_output').scrollHeight;
});

function toggleTheme() {
    const body = document.body;
    const themeButton = document.querySelector('.theme-toggle-button');

    if (body.classList.contains('light-mode')) {
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        themeButton.classList.remove('light-mode');
        themeButton.classList.add('dark-mode');
        themeButton.innerText = 'D'; // Show D in dark theme
        localStorage.setItem('theme', 'dark-mode');
    } else {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        themeButton.classList.remove('dark-mode');
        themeButton.classList.add('light-mode');
        themeButton.innerText = 'L'; // Show L in light theme
        localStorage.setItem('theme', 'light-mode');
    }
}


function openSettings() {
    fetch('/get_options', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        populateOptions(data);
        document.getElementById('settingsModal').style.display = "block";
    });
}

function closeSettings() {
    document.getElementById('settingsModal').style.display = "none";
}

function populateOptions(options) {
    const placeSelect = document.getElementById('place');
    const buildingSelect = document.getElementById('building');
    const floorSelect = document.getElementById('floor');

    placeSelect.innerHTML = '';
    buildingSelect.innerHTML = '';
    floorSelect.innerHTML = '';

    const defaultPlace = "New_York_City";
    const defaultBuilding = "LightHouse";
    const defaultFloor = "6th_floor";

    for (const place in options) {
        const option = document.createElement('option');
        option.value = place;
        option.text = place;
        if (place === defaultPlace) {
            option.selected = true;
        }
        placeSelect.appendChild(option);
    }

    updateBuildingOptions();

    placeSelect.value = defaultPlace;
    buildingSelect.value = defaultBuilding;
    floorSelect.value = defaultFloor;
}

function updateBuildingOptions() {
    const place = document.getElementById('place').value;
    fetch('/get_options', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        const buildingSelect = document.getElementById('building');
        const floorSelect = document.getElementById('floor');

        buildingSelect.innerHTML = '';
        floorSelect.innerHTML = '';

        for (const building in data[place]) {
            const option = document.createElement('option');
            option.value = building;
            option.text = building;
            buildingSelect.appendChild(option);
        }

        updateFloorOptions();
    });
}

function updateFloorOptions() {
    const place = document.getElementById('place').value;
    const building = document.getElementById('building').value;
    fetch('/get_options', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        const floorSelect = document.getElementById('floor');

        floorSelect.innerHTML = '';

        data[place][building].forEach(floor => {
            const option = document.createElement('option');
            option.value = floor;
            option.text = floor;
            floorSelect.appendChild(option);
        });

        updateScale();
    });
}

function updateScale() {
    const place = document.getElementById('place').value;
    const building = document.getElementById('building').value;
    const floor = document.getElementById('floor').value;

    fetch('/get_scale', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ place, building, floor })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('scale').value = data.scale;
    });
}

function openImageBrowser() {
    fetch('/list_images', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        const imageBrowser = document.getElementById('image_browser');
        imageBrowser.innerHTML = '';

        const sortedFolders = Object.keys(data).sort();

        sortedFolders.forEach(id => {
            const idDiv = document.createElement('div');
            idDiv.innerHTML = `<strong>${id}</strong> <span class="folder-toggle">[+]</span>`;
            idDiv.style.cursor = 'pointer';
            idDiv.onclick = function() {
                const imagesDiv = document.getElementById(`images_${id}`);
                const toggleSpan = idDiv.querySelector('.folder-toggle');
                if (imagesDiv.style.display === 'none') {
                    imagesDiv.style.display = 'block';
                    toggleSpan.innerText = '[-]';
                } else {
                    imagesDiv.style.display = 'none';
                    toggleSpan.innerText = '[+]';
                }
            };
            
            const imagesDiv = document.createElement('div');
            imagesDiv.id = `images_${id}`;
            imagesDiv.style.display = 'none';
            imagesDiv.className = 'folder-content';

            const sortedImages = data[id].sort();
            sortedImages.forEach(imageName => {
                const imageLink = document.createElement('a');
                imageLink.href = '#';
                imageLink.innerText = imageName;
                imageLink.onclick = () => selectImage(id, imageName);
                imagesDiv.appendChild(document.createElement('br'));
                imagesDiv.appendChild(imageLink);
            });

            idDiv.appendChild(imagesDiv);
            imageBrowser.appendChild(idDiv);
        });

        document.getElementById('imageBrowserModal').style.display = "block";
    });
}

function closeImageBrowser() {
    document.getElementById('imageBrowserModal').style.display = "none";
}

function selectImage(id, imageName) {
    fetch(`/get_image/${id}/${imageName}`, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        selectedImageBase64 = data.image;
        document.getElementById('query_image_preview').src = `data:image/png;base64,${selectedImageBase64}`;
        initializeOutputs();
        drawFloorplanPreview();
        closeImageBrowser();
    });
}

function initializeOutputs() {
    document.getElementById('pose_output').innerText = 'Pose: ';
    document.getElementById('destination_output').innerText = 'Selected Destination: ';
    document.getElementById('path_output').innerText = 'Path: ';
}

function openSelectDestination() {
    fetch('/get_floorplan_and_destinations', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        socket.emit('log', {data: `Destination data fetched`});
        drawFloorplan(data.floorplan, data.destinations, data.anchors);
        document.getElementById('selectDestinationModal').style.display = "block";
    });
}

function closeSelectDestination() {
    document.getElementById('selectDestinationModal').style.display = "none";
}

function submitSettings() {
    const form = document.getElementById('settingsForm');
    const formData = new FormData(form);
    const settings = {};
    formData.forEach((value, key) => {
        settings[key] = isNaN(value) ? value : parseFloat(value);
    });
    fetch('/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        socket.emit('log', {data: `Settings updated: ${JSON.stringify(data)}`});
        closeSettings();
    });
}

function startServer() {
    fetch('/start', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        socket.emit('log', {data: `Server started: ${data.status}`});
        drawFloorplanPreview();
    });
}

function terminateServer() {
    fetch('/terminate', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        socket.emit('log', {data: `Server terminated: ${data.status}`});
        initializeOutputs();
        document.getElementById('query_image_preview').src = '';
        const canvas = document.getElementById('floorplan_preview');
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    });
}

function localize() {
    fetch('/localize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query_image: selectedImageBase64 })
    })
    .then(response => response.json())
    .then(data => {
        if (data.pose) {
            console.log(data);
            const roundedPose = data.pose.map(coord => Math.round(coord));
            document.getElementById('pose_output').innerText = `Pose: ${JSON.stringify(roundedPose)}`;
            socket.emit('log', {data: `Pose: ${JSON.stringify(roundedPose)}`});
            currentPose = roundedPose;
            drawFloorplanPreview(currentPose, selectedDestination);
        } else {
            document.getElementById('pose_output').innerText = `Pose: Localization failed`;
            socket.emit('log', {data: `Pose: Localization failed`});
        }
    })
    .catch(error => {
        document.getElementById('pose_output').innerText = `Pose: Localization failed`;
        socket.emit('log', {data: `Pose: Localization failed`});
        console.error("Localization error:", error);
    });
}

function drawFloorplan(floorplan, destinations, anchors) {
    const canvas = document.getElementById('floorplan_canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.src = `data:image/png;base64,${floorplan}`;
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0, img.width, img.height);
        drawDestinations(ctx, destinations);
        if (currentPose) {
            drawPose(ctx, currentPose);
        }
    };

    canvas.onclick = function(event) {
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const closestDestination = destinations.reduce((prev, curr) => {
            const prevDistance = Math.hypot(prev.location[0] - x, prev.location[1] - y);
            const currDistance = Math.hypot(curr.location[0] - x, curr.location[1] - y);
            return prevDistance < currDistance ? prev : curr;
        });
        selectedDestination = closestDestination;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, img.width, img.height);
        drawDestinations(ctx, destinations);
        if (currentPose) {
            drawPose(ctx, currentPose);
        }
        ctx.beginPath();
        ctx.arc(closestDestination.location[0], closestDestination.location[1], 10, 0, 2 * Math.PI);
        ctx.fillStyle = 'green';
        ctx.fill();
        document.getElementById('destination_output').innerText = `Selected Destination: ${selectedDestination.name}`;
        document.getElementById('path_output').innerText = '';
    };
}

function drawFloorplanPreview(pose, destination) {
    fetch('/get_floorplan_and_destinations', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        const canvas = document.getElementById('floorplan_preview');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = `data:image/png;base64,${data.floorplan}`;
        img.onload = function() {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            if (destination) {
                drawSelectedDestination(ctx, destination);
            } else {
                drawDestinations(ctx, data.destinations);
            }
            if (pose) {
                drawPose(ctx, pose);
            }
        };
    });
}

function drawDestinations(ctx, destinations) {
    ctx.fillStyle = 'red';
    ctx.font = '12px Arial';
    destinations.forEach((dest, idx) => {
        ctx.beginPath();
        ctx.arc(dest.location[0], dest.location[1], 5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillText(`${idx}: ${dest.name}`, dest.location[0], dest.location[1]);
    });
}

function drawSelectedDestination(ctx, destination) {
    ctx.fillStyle = 'red';
    ctx.font = '100px Arial';
    ctx.beginPath();
    ctx.moveTo(destination.location[0], destination.location[1] - 100);
    ctx.lineTo(destination.location[0] + 50, destination.location[1] + 50);
    ctx.lineTo(destination.location[0] - 100, destination.location[1] - 20);
    ctx.lineTo(destination.location[0] + 100, destination.location[1] - 20);
    ctx.lineTo(destination.location[0] - 50, destination.location[1] + 50);
    ctx.closePath();
    ctx.fill();
    ctx.fillText(destination.name, destination.location[0], destination.location[1]);
}

function drawPose(ctx, pose) {
    const x = pose[0];
    const y = pose[1];
    const angle = pose[2];
    const length = 200;

    const x1 = x - length * Math.sin(angle / 180 * Math.PI);
    const y1 = y - length * Math.cos(angle / 180 * Math.PI);

    ctx.fillStyle = 'blue';
    ctx.beginPath();
    ctx.arc(x, y, 70, 0, 2 * Math.PI);
    ctx.fill();

    ctx.strokeStyle = 'blue';
    ctx.lineWidth = 40;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x1, y1);
    ctx.stroke();
}

function submitDestination() {
    if (selectedDestination) {
        fetch('/select_destination', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({destination_id: selectedDestination.id})
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            socket.emit('log', {data: `Destination selected: ${JSON.stringify(selectedDestination.name)}`});
            drawFloorplanPreview(currentPose, selectedDestination);
            closeSelectDestination();
        });
    } else {
        alert('Please select a destination');
    }
}

function navigate() {
    fetch('/planner', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        const canvas = document.getElementById('floorplan_preview');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = `data:image/png;base64,${data.floorplan}`;
        img.onload = function() {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            drawTrajectory(ctx, data.paths);
        };

        if (data.paths.length <= 1) {
            document.getElementById('path_output').innerText = `Path: Way to destination is blocked`;
        } else {
            const pathList = data.paths.map(path => {
                const x = Math.round(path[0]);
                const y = Math.round(path[1]);
                const floor = path.length > 2 ? path[2] : '';
                return `(${x}, ${y}${floor ? `, ${floor}` : ''})`;
            }).join('<br>');
            document.getElementById('path_output').innerHTML = `Path:<br>${pathList}`;

            const actionList = actions(currentPose, data.paths, parseFloat(document.getElementById('scale').value));
            const actionsOutput = actionList.map(action => `Rotate to ${action[0]} o'clock, Walk ${action[1].toFixed(2)} meters`).join('<br>');
            document.getElementById('path_output').innerHTML += `<br>Actions:<br>${actionsOutput}`;
        }
    })
    .catch(error => {
        console.error("Error in navigate:", error);
    });
}

function drawTrajectory(ctx, paths) {
    for (let i = 1; i < paths.length; i++) {
        const x0 = paths[i - 1][0];
        const y0 = paths[i - 1][1];
        const x1 = paths[i][0];
        const y1 = paths[i][1];

        ctx.strokeStyle = 'green';
        ctx.lineWidth = 40;
        ctx.beginPath();
        ctx.moveTo(x0, y0);
        ctx.lineTo(x1, y1);
        ctx.stroke();
    }

    const start_x = paths[0][0];
    const start_y = paths[0][1];
    ctx.fillStyle = 'blue';
    ctx.beginPath();
    ctx.arc(start_x, start_y, 70, 0, 2 * Math.PI);
    ctx.fill();

    const end_x = paths[paths.length - 1][0];
    const end_y = paths[paths.length - 1][1];

    ctx.fillStyle = 'red';
    ctx.beginPath();
    ctx.moveTo(end_x, end_y - 100);
    ctx.lineTo(end_x + 50, end_y + 50);
    ctx.lineTo(end_x - 100, end_y - 20);
    ctx.lineTo(end_x + 100, end_y - 20);
    ctx.lineTo(end_x - 50, end_y + 50);
    ctx.closePath();
    ctx.fill();
}

window.onclick = function(event) {
    const modalSettings = document.getElementById('settingsModal');
    const modalDestination = document.getElementById('selectDestinationModal');
    const modalImageBrowser = document.getElementById('imageBrowserModal');
    if (event.target === modalSettings) {
        modalSettings.style.display = "none";
    }
    if (event.target === modalDestination) {
        modalDestination.style.display = "none";
    }
    if (event.target === modalImageBrowser) {
        modalImageBrowser.style.display = "none";
    }
}

function goToMonitorPage() {
    // Determine the current theme by checking the body class
    const currentTheme = document.body.classList.contains('dark-mode') ? 'dark-mode' : 'light-mode';
    // Redirect to the monitor page with the theme as a URL parameter
    window.location.href = `/monitor?theme=${currentTheme}`;
}

