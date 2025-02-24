/*
* Provides basic socket function used across all websites
*/
window.socketReady = window.socketReady || $.Deferred();
window.passwordReady
		.then(function(password) {
			// Use the password here
			console.log('Password available:', password);
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
			 }
			 // Display correct socket status
			 socket.on('connect', function(){
			    setSocketStatusDivContent("Connected via SocketIO to the Server. Ready for operation");
			 });
			 // Handle invalid password
			socket.on('invalid_password', function(error) {
				console.error('Seems like you got the wrong password mate. Clearing all cookies...');
                clearAllCookies();
				setSocketStatusDivContent("An invalid password was provided. All cookies were deleted. Please reload the page and try again");
			});

			// Optional: Handle connection errors
			socket.on('disconnect', function(reason) {
				console.log('Server disconnected')
				setSocketStatusDivContent("Server disconnected. Maybe the connection is broken or the server has been shut down?")
			});
			 window.socketReady.resolve(socket);
			});

		}