function validateRegister() {
    var pass = document.getElementById("password").value;
    var confirm = document.getElementById("confirm_password").value;
    if (pass !== confirm) {
        alert("Passwords do not match!");
        return false;
    }
    return true;
}

var roleSelect = document.getElementById("role");
if (roleSelect) {
    roleSelect.addEventListener("change", function() {
        var adminDiv = document.getElementById("admin-code-div");
        if (this.value === "admin") {
            adminDiv.style.display = "block";
        } else {
            adminDiv.style.display = "none";
        }
    });
}