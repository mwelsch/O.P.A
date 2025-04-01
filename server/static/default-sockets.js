/*
* Provides basic socket function used across all websites
*/
window.socketReady = window.socketReady || $.Deferred();
window.liveStreamCapabilities = window.liveStreamCapabilities || $.Deferred();
window.executeCapabilities = window.executeCapabilities || $.Deferred();

window.passwordReady
    .then(function(password) {
        // Use the password here
        console.log('Password Ready:', password);
        initializeSocketConnection(password);
    })
    .fail(function(error) {
        console.error('Password error:', error);
        handlePasswordError(error);
    });
function clearAllCookies(){
    const cookies = document.cookie.split('; ');
    // Set expiration date to past for each cookie
    cookies.forEach(cookie => {
        const [name] = cookie.split('=');
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
    });
}

function setSocketStatusDivContent(newStatus){
    const container = $('#socketio-status');
    container.empty();  // Clear current status
    container.append("<h1>"+newStatus+"</h1>");
}



function initializeSocketConnection(password) {
     setSocketStatusDivContent("Creating socketIO. As long as you see this, the connection is not working properly")
     const socket = io({
     auth: {
         password: password
     }});
     // Display correct socket status
     socket.on('connect', function(){
        setSocketStatusDivContent("Connected via SocketIO to the Server. Ready for operation");
        console.log('Connected successfully via SocketIO.');

     });
     // Handle connection error. Gets thrown with invalid passwordsinvalid password
    socket.on("connect_error", (error) => {
          if (socket.active) {
            // temporary failure, the socket will automatically try to reconnect
            console.log("Temoparary socket connection error")
          } else {
            // the connection was denied by the server
            // in that case, `socket.connect()` must be manually called in order to reconnect
            console.log(error.message);
            clearAllCookies();
            setSocketStatusDivContent("Connect Error. Cleared Saved Password because this behaviour is only expected when you provide a wrong password. Reloading page in 10 seconds...")
            setTimeout(function() {
                location.reload();
            }, 10000);
          }
        });



    // Optional: Handle connection errors
    socket.on('disconnect', function(reason) {

        console.log('Server disconnected. Reason:' + reason)
        setSocketStatusDivContent("Server disconnected. Maybe the connection is broken or the server has been shut down?")
    });
    window.liveStreamCapabilities.resolve(socket);
    window.executeCapabilities.resolve(socket);
    window.socketReady.resolve(socket);
}