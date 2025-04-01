window.liveStreamCapabilities.then(function(socket) {

    socket.on('output_of_command', ({type, data}) => {
        console.log("receiving output data from a command");
        console.log(data);
        if(data){
        //ToDO check if command output matches the client, currently displaying all outputs...
            $('#command_output').empty();
            $('#command_output').html(data);

        }

    });

     $("#execute-btn").click(function(){
        execute(socket, document.getElementById('command_content').value);
     });

});

function execute(socket, command){
    socket.emit("execute", getUrlParameter("payload_id"), command);
    console.log("Executed command for payload" + getUrlParameter("payload_id") + " Command: " + command)
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
