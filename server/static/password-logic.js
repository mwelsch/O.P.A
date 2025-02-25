window.passwordReady = window.passwordReady || $.Deferred();
function setCookie(name, value, days) {
      const d = new Date();
      d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000)); // days -> milliseconds
      const expires = "expires=" + d.toUTCString();
      document.cookie = name + "=" + encodeURIComponent(value) + ";" + expires + ";path=/";
    }

// Retrieve a cookie value by its name
function getCookie(name) {
  const decodedCookie = decodeURIComponent(document.cookie);
  const cookieArray = decodedCookie.split(';');
  for (let i = 0; i < cookieArray.length; i++) {
    let c = cookieArray[i].trim();
    if (c.indexOf(name + "=") === 0) {
      return c.substring(name.length + 1);
    }
  }
  return "";
}
function getOrPromptPassword(){
    let storedPassword = getCookie("user_password");
    if (!storedPassword) {
    // If not found, prompt the user to enter a new password
    const enteredPassword = prompt("Enter your password:");
    if (enteredPassword && enteredPassword.trim().length > 0) {
      // Save the new password in a cookie for 1 day
      setCookie("user_password", enteredPassword, 1);
      alert("Password saved in cookie for 24 hours!");
      storedPassword = enteredPassword
    } else {
      alert("No password entered, and no cookie set.");
    }
    }

    console.log("PASSWORD COOKIE:")
    console.log(storedPassword)
    console.log("Calling the promise with the loaded password...")
    window.passwordReady.resolve(storedPassword);
}
$(document).ready(function(){
    getOrPromptPassword();
});