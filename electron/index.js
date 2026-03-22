document.onkeydown = updateKey;
document.onkeyup = resetKey;

// Add button event listeners
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('upButton').addEventListener('click', function() {
        showButtonPressed('upButton', 'upArrow');
        send_data('FORWARD');
    });
    document.getElementById('downButton').addEventListener('click', function() {
        showButtonPressed('downButton', 'downArrow');
        send_data('BACKWARD');
    });
    document.getElementById('leftButton').addEventListener('click', function() {
        showButtonPressed('leftButton', 'leftArrow');
        send_data('LEFT');
    });
    document.getElementById('rightButton').addEventListener('click', function() {
        showButtonPressed('rightButton', 'rightArrow');
        send_data('RIGHT');
    });
});

// Use the IP address from your working curl command
var server_port = 65432;
var server_addr = "192.168.68.92"; 
var base_url = `http://${server_addr}:${server_port}`;

async function send_data(command) {
    try {
        // This fetch call performs the exact same action as your curl -X POST
        const response = await fetch(`${base_url}/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // The body must be a JSON string: '{"command": "forward"}'
            body: JSON.stringify({ "command": command.toLowerCase() })
        });

        const data = await response.json();
        console.log('Server response:', data);
        
        if (data.status === "ok" && data.telemetry) {
            updateUI(data.telemetry);
        }
    } catch (error) {
        console.error('Network error:', error);
        document.getElementById("bluetooth").innerHTML = "Connection Failed";
    }
}

// Helper to update the HTML spans with new data
function updateUI(telemetry) {
    document.getElementById("direction").innerHTML = telemetry.direction;
    document.getElementById("speed").innerHTML = telemetry.speed;
    document.getElementById("temperature").innerHTML = telemetry.temperature;
    document.getElementById("battery").innerHTML = telemetry.battery_percentage;
    document.getElementById("battery_voltage").innerHTML = telemetry.battery_voltage;
}

// Replace the old client() function to fetch telemetry
async function client() {
    try {
        const response = await fetch(`${base_url}/telemetry`);
        const data = await response.json();
        updateUI(data);
    } catch (e) {
        console.error("Telemetry update failed", e);
    }
}

// for detecting which key is been pressed w,a,s,d
function updateKey(e) {

    e = e || window.event;

    if (e.keyCode == '87') {
        // up (w)
        document.getElementById("upArrow").style.color = "green";
        send_data("FORWARD");
    }
    else if (e.keyCode == '83') {
        // down (s)
        document.getElementById("downArrow").style.color = "green";
        send_data("BACKWARD");
    }
    else if (e.keyCode == '65') {
        // left (a)
        document.getElementById("leftArrow").style.color = "green";
        send_data("LEFT");
    }
    else if (e.keyCode == '68') {
        // right (d)
        document.getElementById("rightArrow").style.color = "green";
        send_data("RIGHT");
    }
}

// reset the key to the start state 
function resetKey(e) {

    e = e || window.event;

    document.getElementById("upArrow").style.color = "grey";
    document.getElementById("downArrow").style.color = "grey";
    document.getElementById("leftArrow").style.color = "grey";
    document.getElementById("rightArrow").style.color = "grey";
}

// Button press visual feedback
function showButtonPressed(buttonId, arrowId) {
    document.getElementById(arrowId).style.color = "green";
    setTimeout(() => {
        document.getElementById(arrowId).style.color = "grey";
    }, 200);
}


// Auto-poll telemetry every 500ms on load
document.addEventListener('DOMContentLoaded', function() {
    setInterval(client, 500);
});
