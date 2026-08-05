/* ==========================
   ROLE SELECTION
========================== */

let selectedRole = "student";

function selectRole(role, button) {

    selectedRole = role;

    document.getElementById("selectedRole").value = role;

    document.querySelectorAll(".role-btn")
        .forEach(btn => btn.classList.remove("active"));

    button.classList.add("active");

    const label = document.getElementById("passwordLabel");
    const passwordField = document.getElementById("password");

    if (role === "student") {

        label.innerHTML = "Password (DD/MM/YYYY)";
        passwordField.placeholder = "DD/MM/YYYY";

    }
    else if (role === "owner") {

        label.innerHTML = "Owner Password";
        passwordField.placeholder = "Enter Owner Password";

    }
    else {

        label.innerHTML = "Admin Password";
        passwordField.placeholder = "Enter Admin Password";

    }
}

/* ==========================
   SHOW / HIDE PASSWORD
========================== */

const togglePassword = document.getElementById("togglePassword");
const passwordField = document.getElementById("password");

togglePassword.addEventListener("click", () => {

    if (passwordField.type === "password") {

        passwordField.type = "text";
        togglePassword.textContent = "🔒";

    } else {

        passwordField.type = "password";
        togglePassword.textContent = "👁";

    }

});

/* ==========================
   LOGIN VALIDATION
========================== */

document.getElementById("loginForm")
.addEventListener("submit", function (e) {

    e.preventDefault();

    const username =
        document.getElementById("username")
        .value.trim();

    const password =
        document.getElementById("password")
        .value.trim();

    const errorMsg =
        document.getElementById("errorMsg");

    const successMsg =
        document.getElementById("successMsg");

    errorMsg.innerHTML = "";
    successMsg.innerHTML = "";

    /* Empty Validation */

    if (username === "") {

        errorMsg.innerHTML =
            "Please enter Username / Register Number";

        return;
    }

    if (password === "") {

        errorMsg.innerHTML =
            "Please enter Password";

        return;
    }

    /* Student Validation */

    if (selectedRole === "student") {

        const regNoPattern = /^[0-9]+$/;

        const dobPattern =
            /^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/(19|20)\d{2}$/;

        if (!regNoPattern.test(username)) {

            errorMsg.innerHTML =
                "Register Number must contain numbers only";

            return;
        }

        if (!dobPattern.test(password)) {

            errorMsg.innerHTML =
                "DOB must be in DD/MM/YYYY format";

            return;
        }
    }

    /* Owner Validation */

    if (selectedRole === "owner") {

        if (username.length < 3) {

            errorMsg.innerHTML =
                "Owner username is too short";

            return;
        }

        if (password.length < 3) {

            errorMsg.innerHTML =
                "Owner password is too short";

            return;
        }
    }

    /* Admin Validation */

    if (selectedRole === "admin") {

        if (username.length < 3) {

            errorMsg.innerHTML =
                "Admin username is too short";

            return;
        }

        if (password.length < 3) {

            errorMsg.innerHTML =
                "Admin password is too short";

            return;
        }
    }

    successMsg.innerHTML =
        "Checking credentials...";

    /* Submit to Flask */

    document.getElementById("loginForm").submit();

});
