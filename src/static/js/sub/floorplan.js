// floorplan.js

const socket = io();
let sessionId;

document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    sessionId = urlParams.get('session_id');

    if (!sessionId) {
        console.error('No session ID provided');
        return;
    }

    socket.emit('join_room', { session_id: sessionId });

    socket.on('planner_update', function(data) {
        drawFloorplan(data.floorplan, data.paths);
    });

    socket.on('camera_frame', function(data) {
        if (data.session_id === sessionId) {
            document.getElementById('live_stream').src = `data:image/jpeg;base64,${data.frame}`;
        }
    });
});

function drawFloorplan(floorplan, trajectory) {
    const canvas = document.getElementById('floorplan_canvas');
    const ctx = canvas.getContext('2d');

    let scale = 1;
    let originX = 0;
    let originY = 0;
    let isDragging = false;
    let startX, startY;

    const img = new Image();
    img.src = `data:image/png;base64,${floorplan}`;
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0, img.width, img.height);

        if (trajectory && trajectory.length > 0) {
            // Extract the first element as the pose
            const pose = trajectory[0];

            // Draw the remaining trajectory (excluding the first element)
            const remainingTrajectory = trajectory.slice(1);

            // Draw the pose
            drawPose(ctx, pose);

            // Draw the trajectory including the line from pose to the first point in remainingTrajectory
            drawTrajectory(ctx, pose, remainingTrajectory);
        }
    };

    // // Zoom functionality
    // canvas.addEventListener('wheel', function(event) {
    //     event.preventDefault();
    //     const { offsetX, offsetY, deltaY } = event;

    //     const zoomIntensity = 0.2; // Increase zoom speed
    //     const zoom = Math.exp(deltaY * -zoomIntensity);

    //     const newScale = scale * zoom;

    //     // Calculate the new origin after zooming
    //     originX -= (offsetX / scale - offsetX / newScale);
    //     originY -= (offsetY / scale - offsetY / newScale);

    //     scale = newScale;
    //     draw();
    // });

    // Drag functionality
    canvas.addEventListener('mousedown', function(event) {
        isDragging = true;
        startX = event.clientX;
        startY = event.clientY;
        canvas.style.cursor = 'grabbing';
    });

    canvas.addEventListener('mousemove', function(event) {
        if (isDragging) {
            const dx = event.clientX - startX;
            const dy = event.clientY - startY;

            originX += dx / scale; 
            originY += dy / scale;

            startX = event.clientX;
            startY = event.clientY;

            draw();
        }
    });

    canvas.addEventListener('mouseup', function() {
        isDragging = false;
        canvas.style.cursor = 'grab';
    });

    canvas.addEventListener('mouseleave', function() {
        isDragging = false;
        canvas.style.cursor = 'grab';
    });

    // Function to redraw the canvas with updated transformations
    function draw() {
        ctx.save();
        ctx.setTransform(scale, 0, 0, scale, -originX * scale, -originY * scale);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, img.width, img.height);

        if (trajectory && trajectory.length > 0) {
            const pose = trajectory[0];
            const remainingTrajectory = trajectory.slice(1);
            drawPose(ctx, pose);
            drawTrajectory(ctx, pose, remainingTrajectory);
        }
        ctx.restore();
    }

    // Set the initial cursor style
    canvas.style.cursor = 'grab';
}

function drawPose(ctx, pose) {
    const x = pose[0];
    const y = pose[1];
    const angle = pose.length > 2 ? pose[2] : 0;  // Angle is optional
    const length = 50;

    const x1 = x - length * Math.sin(angle * Math.PI / 180);
    const y1 = y - length * Math.cos(angle * Math.PI / 180);

    ctx.fillStyle = 'blue';
    ctx.beginPath();
    ctx.arc(x, y, 50, 0, 2 * Math.PI); // Increase point size
    ctx.fill();

    ctx.strokeStyle = 'blue';
    ctx.lineWidth = 15; // Thicken the line
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x1, y1);
    ctx.stroke();
}

function drawTrajectory(ctx, pose, trajectory) {
    ctx.strokeStyle = 'orange';
    ctx.lineWidth = 15; // Thicken the line

    // Start from the pose
    ctx.beginPath();
    ctx.moveTo(pose[0], pose[1]);

    // Draw the line from the pose to the first point in the trajectory
    if (trajectory.length > 0) {
        ctx.lineTo(trajectory[0][0], trajectory[0][1]);
    }

    // Continue drawing the rest of the trajectory
    trajectory.forEach((point, index) => {
        if (index === trajectory.length - 1) {
            drawStar(ctx, point[0], point[1], 50);
        } else {
            ctx.lineTo(point[0], point[1]);
        }
    });

    ctx.stroke();
}

function drawStar(ctx, x, y, size) {
    ctx.fillStyle = 'red';

    ctx.beginPath();
    ctx.moveTo(x, y - size);  // Top
    ctx.lineTo(x + size * 0.588, y + size * 0.809);  // Bottom right
    ctx.lineTo(x - size * 0.951, y - size * 0.309);  // Top left
    ctx.lineTo(x + size * 0.951, y - size * 0.309);  // Top right
    ctx.lineTo(x - size * 0.588, y + size * 0.809);  // Bottom left
    ctx.closePath();

    ctx.fill();
}
