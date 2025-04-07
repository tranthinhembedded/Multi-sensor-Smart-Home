const doorFront = document.querySelector(".door-front");
const loginForm = document.getElementById("login-form");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const exitButton = document.getElementById("exit-button");
const loginContainer = document.querySelector(".login-container");
const loginButton = document.getElementById("login-button");
const faceIdButton = document.getElementById("face-id-button");

// Admin infor
const validUsername = "admin";
const validPassword = "123456";

// Close door
function closeDoor() {
  doorFront.style.transform = "rotateY(0deg)"; // ?óng c?a trên giao di?n
  fetch('/close_door')
    .then(response => response.text())
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));
}

// X? lý ??ng nh?p
loginForm.addEventListener("submit", (event) => {
  event.preventDefault(); // Ng?n form g?i m?c ??nh

  const username = usernameInput.value;
  const password = passwordInput.value;

  // Ki?m tra thông tin ??ng nh?p
  if (username === validUsername && password === validPassword) {
    // M? c?a trên giao di?n
    doorFront.style.transform = "rotateY(-160deg)";

    // G?i yêu c?u m? c?a th?t (servo quay 90 ??)
    fetch('/open_door')
      .then(response => response.text())
      .then(data => console.log(data))
      .catch(error => console.error('Error:', error));

    // T? ??ng ?óng c?a sau 10 giây
    setTimeout(closeDoor, 5000);

    loginContainer.style.display = "none";
    usernameInput.value = "";
    passwordInput.value = "";
  } else {
    // Báo l?i n?u ??ng nh?p sai
    alert("Incorrect Username or Password. Please try again.");
  }
});

// Nút thoát
exitButton.addEventListener("click", () => {
  loginContainer.style.display = "none"; // ?óng form ??ng nh?p
  usernameInput.value = "";
  passwordInput.value = "";
});

// Nút ??ng nh?p
loginButton.addEventListener("click", () => {
  loginContainer.style.display = "block";
});

// Face ID button handler
faceIdButton.addEventListener("click", () => {
  fetch('/start_face_id')
    .then(response => response.text())
    .then(data => {
      console.log(data);
      alert("Face ID recognition started!");
    })
    .catch(error => console.error('Error:', error));
});
