window.liveStreamCapabilities.then(function(socket) {
    socket.on('newest_image_returned', ({type, data}) => {
            if (data) {
                $('#last_image').html('<img src="data:image/png;base64,' + data + '" alt="Newest Image" style="max-width: 100%;">');
        }
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

});
function startLiveStream(socket){
    socket.emit("start_live_stream");

}
function stopLiveStream(socket){
    socket.emit("stop_live_stream"); //ToDo Implement on the server side
}
