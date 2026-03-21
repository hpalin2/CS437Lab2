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

var server_port = 65432;
var server_addr = "127.0.0.1";   // the IP address of your Raspberry PI

// Send data to the Pi server
function send_data(command) {
    const net = require('net');
    
    const client = net.createConnection({ port: server_port, host: server_addr }, () => {
        console.log('connected to server!');
        // send the command
        client.write(`${command}\r\n`);
    });
    
    // get the data from the server
    client.on('data', (data) => {
        const dataStr = data.toString().trim();
        console.log('Received from server:', dataStr);
        
        // Parse the received data
        try {
            // Try to parse as JSON first (for structured data like battery, temp, etc)
            const jsonData = JSON.parse(dataStr);
            if (jsonData.battery !== undefined) {
                document.getElementById("battery").innerHTML = jsonData.battery.toFixed(1) + '%';
            }
            if (jsonData.temperature !== undefined) {
                document.getElementById("temperature").innerHTML = jsonData.temperature.toFixed(1);
            }
            if (jsonData.distance !== undefined) {
                document.getElementById("distance").innerHTML = jsonData.distance.toFixed(1);
            }
            if (jsonData.speed !== undefined) {
                document.getElementById("speed").innerHTML = jsonData.speed.toFixed(1);
            }
            if (jsonData.direction !== undefined) {
                document.getElementById("direction").innerHTML = jsonData.direction;
            }
        } catch (e) {
            // If not JSON, just display as string
            document.getElementById("bluetooth").innerHTML = dataStr;
        }
        
        client.end();
        client.destroy();
    });

    client.on('error', (err) => {
        console.error('Connection error:', err);
        client.destroy();
    });

    client.on('end', () => {
        console.log('disconnected from server');
    });
}

function client(){
    
    const net = require('net');
    var input = document.getElementById("message").value;

    const client = net.createConnection({ port: server_port, host: server_addr }, () => {
        // 'connect' listener.
        console.log('connected to server!');
        // send the message
        client.write(`${input}\r\n`);
    });
    
    // get the data from the server
    client.on('data', (data) => {
        document.getElementById("bluetooth").innerHTML = data;
        console.log(data.toString());
        client.end();
        client.destroy();
    });

    client.on('end', () => {
        console.log('disconnected from server');
    });


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


// update data for every 50ms
function update_data(){
    setInterval(function(){
        // get image from python server
        client();
    }, 50);
}
