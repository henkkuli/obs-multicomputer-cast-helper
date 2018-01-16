let socket = io();
let settings = {};
let previews = [];
const textDecoder = new TextDecoder('utf-8');
const textEncoder = new TextEncoder('utf-8');

function handleMessage(event) {
}

function changePreview(preview, remote) {
    socket.emit('change_preview', { preview_number: preview, remote_number: remote });
}

function createPreviews() {
    const container = $("#preview-container");
    const template = $("#preview-template");

    container.empty();

    previews = [];
    for (let preview_number = 1; preview_number <= settings.number_of_previews; preview_number++) {
        const preview = template.clone();
        preview.removeClass("d-none");
        preview.find('.name').text(`Preview ${preview_number}`);
        preview.find('.change-preview').on('click', () => changePreview(preview_number, 1));

        container.append(preview);
        previews.push(preview);
    }
}

$(function() {
    // TODO: Support wss
    //const socket_url = `ws://${window.location.host}/socket`;
    //let socket = new WebSocket(socket_url);

    socket.on("connect", function(event) {
        console.log("Connected to the server");
        socket.emit('client_connected', {});
    });
    socket.on("error", function(event) {
        console.log("Error with the server connection");
    });
    socket.on("welcome", function(data) {
        console.log("Welcome received");
        settings = data;

        createPreviews();
    });

    socket.on("log", function(data) {
        const preview = data.preview_number;
        const log = data.log;
        console.log(arguments);
        const log_string = log.map(line => textDecoder.decode(line)).join('');

        previews[preview].find('.log').text(log_string);
    });
    socket.on("bear", function(data) {
        console.log("Heatbeat");
    });

    $('.change-preview').on('click', function(event) {
        alert(arguments);
    });
});
