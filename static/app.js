
function handleMessage(event) {
}

$(function() {
    // TODO: Support wss
    //const socket_url = `ws://${window.location.host}/socket`;
    //let socket = new WebSocket(socket_url);
    let socket = io();

    socket.on("connect", function(event) {
        console.log("Connected to the server");
        socket.emit('client_connected', {});
    });
    socket.on("error", function(event) {
        console.log("Error with the server connection");
    });
    socket.on("welcome", function(event) {
        console.log("I feel welcome");
    });

    socket.addEventListener("message", handleMessage);
});
