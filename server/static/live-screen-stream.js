window.liveStreamCapabilities.then(function(socket) {
    socket.on('newest_image_returned', ({type, data}) => {
            if (data) {
                $('#last_image').empty();
                $('#last_image').html('<img src="data:image/png;base64,' + data + '" alt="Newest Image" style="max-width: 100%;">');
            }
    });

    socket.on('connect', function(){
        socket.emit('request_clients');
    });
    socket.on('update_clients', function(clients) {
        var clientStillAvailable = checkAvailabilityOfClient(clients);
        if (clientStillAvailable == false){
            location.href = "/";
        }
    });

    $("#toggle-btn").click(function(){
        if ($("#toggle-btn").text() == "Start Livestream"){
            startLiveStream(socket);
            $("#toggle-btn").html("Stop Livestream");
        } else {
            stopLiveStream(socket);
            $("#toggle-btn").html("Start Livestream");
        }
        });
});

function startLiveStream(socket){
    socket.emit("start_live_stream", getUrlParameter("payload_id"));
    console.log("Starting live screen stream for" + getUrlParameter("payload_id"))
}
function checkAvailabilityOfClient(clients){
    var target = getUrlParameter("payload_id");
    var retu_value = false;
    clients.forEach(function(client) {
        if (client === target){
            retu_value = true;
        }
    });
    return retu_value;
}
function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    var sParameterName;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
    return false;
}
function stopLiveStream(socket){
    socket.emit("stop_live_stream", getUrlParameter("payload_id")); //ToDo Implement on the server side
}
