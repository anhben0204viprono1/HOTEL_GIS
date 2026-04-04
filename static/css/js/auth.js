// static/js/auth.js
// Authentication functionality

document.addEventListener("DOMContentLoaded", () => {
  // Check authentication status
  checkAuthStatus();

  // Initialize login page
  if (document.getElementById("loginForm")) {
    initLoginPage();
  }

  // Initialize register page
  if (document.getElementById("registerForm")) {
    initRegisterPage();
  }
});

// Check if user is authenticated
async function checkAuthStatus() {
  try {
    const response = await fetch("/api/auth/check");
    const data = await response.json();

    if (data.success && data.authenticated) {
      updateUIForLoggedInUser(data.customer);
    } else {
      updateUIForGuest();
    }
  } catch (error) {
    console.error("Error checking auth status:", error);
  }
}

function updateUIForLoggedInUser(customer) {
  const loginBtn = document.querySelector(".btn-login");
  if (loginBtn) {
    loginBtn.textContent = customer.full_name;
    loginBtn.href = "/profile";

    // Add dropdown menu
    const dropdown = document.createElement("div");
    dropdown.className = "user-dropdown";
    dropdown.innerHTML = `
            <a href="/profile"><i class="fas fa-user"></i> Trang cá nhân</a>
            <a href="/my-bookings"><i class="fas fa-calendar"></i> Đơn đặt phòng</a>
            <a href="#" id="logoutBtn"><i class="fas fa-sign-out-alt"></i> Đăng xuất</a>
        `;
    loginBtn.parentElement.appendChild(dropdown);

    // Logout handler
    document
      .getElementById("logoutBtn")
      .addEventListener("click", async (e) => {
        e.preventDefault();
        await logout();
      });
  }
}

function updateUIForGuest() {
  // Keep default login button
}

// Login Page
function initLoginPage() {
  const loginForm = document.getElementById("loginForm");
  const togglePassword = document.getElementById("togglePassword");
  const passwordInput = document.getElementById("password");
  const forgotPasswordLink = document.getElementById("forgotPasswordLink");

  // Toggle password visibility
  if (togglePassword) {
    togglePassword.addEventListener("click", () => {
      const type = passwordInput.type === "password" ? "text" : "password";
      passwordInput.type = type;
      togglePassword.classList.toggle("fa-eye");
      togglePassword.classList.toggle("fa-eye-slash");
    });
  }

  // Login form submission
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    await handleLogin();
  });

  // Forgot password
  if (forgotPasswordLink) {
    forgotPasswordLink.addEventListener("click", (e) => {
      e.preventDefault();
      document.getElementById("forgotPasswordModal").style.display = "flex";
    });
  }

  // Forgot password form
  const forgotPasswordForm = document.getElementById("forgotPasswordForm");
  if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await handleForgotPassword();
    });
  }

  // Close forgot password modal
  document
    .querySelectorAll(".modal-close, #closeForgotModal")
    .forEach((btn) => {
      btn.addEventListener("click", () => {
        document.getElementById("forgotPasswordModal").style.display = "none";
      });
    });

  // Social login buttons (placeholder)
  document.getElementById("googleLogin")?.addEventListener("click", () => {
    utils.showToast("Tính năng đăng nhập Google sẽ sớm ra mắt", "info");
  });

  document.getElementById("facebookLogin")?.addEventListener("click", () => {
    utils.showToast("Tính năng đăng nhập Facebook sẽ sớm ra mắt", "info");
  });
}

async function handleLogin() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const loginBtn = document.getElementById("loginBtn");

  // Validate
  if (!email || !password) {
    utils.showToast("Vui lòng nhập đầy đủ thông tin", "warning");
    return;
  }

  try {
    loginBtn.disabled = true;
    loginBtn.innerHTML =
      '<i class="fas fa-spinner fa-spin"></i> Đang đăng nhập...';

    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (data.success) {
      utils.showToast("Đăng nhập thành công!", "success");

      // Redirect to previous page or home
      const redirect = utils.getQueryParam("redirect") || "/";
      setTimeout(() => {
        window.location.href = redirect;
      }, 1000);
    } else {
      utils.showToast(data.message, "danger");
      loginBtn.disabled = false;
      loginBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Đăng nhập';
    }
  } catch (error) {
    console.error("Login error:", error);
    utils.showToast("Có lỗi xảy ra, vui lòng thử lại", "danger");
    loginBtn.disabled = false;
    loginBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Đăng nhập';
  }
}

async function handleForgotPassword() {
  const email = document.getElementById("resetEmail").value;

  if (!email) {
    utils.showToast("Vui lòng nhập email", "warning");
    return;
  }

  try {
    const response = await fetch("/api/auth/forgot-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email }),
    });

    const data = await response.json();

    if (data.success) {
      utils.showToast(
        "Link đặt lại mật khẩu đã được gửi đến email của bạn",
        "success",
      );
      document.getElementById("forgotPasswordModal").style.display = "none";
    } else {
      utils.showToast(data.message, "danger");
    }
  } catch (error) {
    console.error("Forgot password error:", error);
    utils.showToast("Có lỗi xảy ra, vui lòng thử lại", "danger");
  }
}

// Register Page
function initRegisterPage() {
  const registerForm = document.getElementById("registerForm");
  const togglePassword = document.getElementById("togglePassword");
  const toggleConfirmPassword = document.getElementById(
    "toggleConfirmPassword",
  );
  const passwordInput = document.getElementById("password");
  const confirmPasswordInput = document.getElementById("confirmPassword");

  // Toggle password visibility
  if (togglePassword) {
    togglePassword.addEventListener("click", () => {
      const type = passwordInput.type === "password" ? "text" : "password";
      passwordInput.type = type;
      togglePassword.classList.toggle("fa-eye");
      togglePassword.classList.toggle("fa-eye-slash");
    });
  }

  if (toggleConfirmPassword) {
    toggleConfirmPassword.addEventListener("click", () => {
      const type =
        confirmPasswordInput.type === "password" ? "text" : "password";
      confirmPasswordInput.type = type;
      toggleConfirmPassword.classList.toggle("fa-eye");
      toggleConfirmPassword.classList.toggle("fa-eye-slash");
    });
  }

  // Password strength checker
  passwordInput.addEventListener("input", () => {
    checkPasswordStrength(passwordInput.value);
  });

  // Confirm password validation
  confirmPasswordInput.addEventListener("input", () => {
    validateConfirmPassword();
  });

  // Register form submission
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    await handleRegister();
  });
}

function checkPasswordStrength(password) {
  const strengthBar = document.getElementById("passwordStrengthBar");
  const strengthText = document.getElementById("passwordStrengthText");

  let strength = 0;
  let text = "";
  let color = "";

  if (password.length >= 6) strength += 20;
  if (password.length >= 8) strength += 20;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 20;
  if (/\d/.test(password)) strength += 20;
  if (/[^a-zA-Z\d]/.test(password)) strength += 20;

  if (strength <= 40) {
    text = "Yếu";
    color = "#E74C3C";
  } else if (strength <= 60) {
    text = "Trung bình";
    color = "#F39C12";
  } else if (strength <= 80) {
    text = "Khá";
    color = "#3498DB";
  } else {
    text = "Mạnh";
    color = "#2ECC71";
  }

  strengthBar.style.width = strength + "%";
  strengthBar.style.backgroundColor = color;
  strengthText.textContent = text;
  strengthText.style.color = color;
}

function validateConfirmPassword() {
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirmPassword").value;
  const confirmInput = document.getElementById("confirmPassword");

  if (confirmPassword && password !== confirmPassword) {
    confirmInput.setCustomValidity("Mật khẩu không khớp");
    confirmInput.style.borderColor = "#E74C3C";
  } else {
    confirmInput.setCustomValidity("");
    confirmInput.style.borderColor = "";
  }
}

async function handleRegister() {
  const fullName = document.getElementById("fullName").value;
  const email = document.getElementById("email").value;
  const phone = document.getElementById("phone").value;
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirmPassword").value;
  const idCard = document.getElementById("idCard").value;
  const dateOfBirth = document.getElementById("dateOfBirth").value;
  const address = document.getElementById("address").value;
  const agreeTerms = document.getElementById("agreeTerms").checked;
  const registerBtn = document.getElementById("registerBtn");

  // Validate
  if (!fullName || !email || !password) {
    utils.showToast("Vui lòng nhập đầy đủ thông tin bắt buộc", "warning");
    return;
  }

  if (password !== confirmPassword) {
    utils.showToast("Mật khẩu không khớp", "warning");
    return;
  }

  if (password.length < 6) {
    utils.showToast("Mật khẩu phải có ít nhất 6 ký tự", "warning");
    return;
  }

  if (!agreeTerms) {
    utils.showToast("Vui lòng đồng ý với điều khoản dịch vụ", "warning");
    return;
  }

  try {
    registerBtn.disabled = true;
    registerBtn.innerHTML =
      '<i class="fas fa-spinner fa-spin"></i> Đang đăng ký...';

    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        full_name: fullName,
        email: email,
        phone_number: phone,
        password: password,
        id_card_number: idCard,
        date_of_birth: dateOfBirth,
        address: address,
      }),
    });

    const data = await response.json();

    if (data.success) {
      utils.showToast(
        "Đăng ký thành công! Đang chuyển đến trang đăng nhập...",
        "success",
      );
      setTimeout(() => {
        window.location.href = "/login";
      }, 2000);
    } else {
      utils.showToast(data.message, "danger");
      registerBtn.disabled = false;
      registerBtn.innerHTML = '<i class="fas fa-user-plus"></i> Đăng ký';
    }
  } catch (error) {
    console.error("Register error:", error);
    utils.showToast("Có lỗi xảy ra, vui lòng thử lại", "danger");
    registerBtn.disabled = false;
    registerBtn.innerHTML = '<i class="fas fa-user-plus"></i> Đăng ký';
  }
}

// Logout function
async function logout() {
  try {
    const response = await fetch("/api/auth/logout", {
      method: "POST",
    });

    const data = await response.json();

    if (data.success) {
      utils.showToast("Đã đăng xuất", "success");
      setTimeout(() => {
        window.location.href = "/";
      }, 1000);
    }
  } catch (error) {
    console.error("Logout error:", error);
    utils.showToast("Có lỗi xảy ra", "danger");
  }
}

// Export functions
window.logout = logout;
