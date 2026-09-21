import { icons } from "../components/icons.js";
import { toast } from "../components/ui.js";
import { api } from "../api.js";
import { navigate, updateAuthStateCache } from "../router.js";
import { mountNav } from "../components/nav.js";
import { store, updateAuthState } from "../store.js";

export async function render(container) {
  container.innerHTML = `
    <div class="auth-page">
      <div class="auth-container">
        <div class="auth-brand">
          <span class="auth-brand__mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
              <path d="M12 21v-8" /><path d="M12 13c0-4 3-6 7-6 0 4-3 7-7 7" /><path d="M12 13c0-3-2.5-5-5.5-5C6 11 8.5 13.5 12 13.5" />
            </svg>
          </span>
          <div><h1>AgriSense AI</h1><p class="auth-brand__tagline">Intelligent Multi-Agent Farming Assistant</p></div>
        </div>

        <div class="auth-card">
          <div class="auth-card__head">
            <h2>Create your account</h2>
            <p>Join AgriSense AI for clear soil, crop health, weather and market intelligence in one place.</p>
          </div>

          <form id="register-form" class="stack-form auth-form">
            <div class="field">
              <label for="name">Full Name <span class="required">*</span></label>
              <input
                type="text"
                id="name"
                name="name"
                placeholder="Your full name"
                required
                autocomplete="name"
              />
            </div>

            <div class="field">
              <label for="email">Email <span class="required">*</span></label>
              <input
                type="text"
                id="email"
                name="email"
                placeholder="your@email.com"
                required
                autocomplete="email"
              />
            </div>

            <div class="field">
              <label for="password">Password <span class="required">*</span></label>
              <div class="field-hint">At least 8 characters</div>
              <div class="field-password-input">
                <input
                  type="password"
                  id="password"
                  name="password"
                  placeholder="••••••••"
                  required
                  autocomplete="new-password"
                  minlength="8"
                />
              </div>
            </div>

            <div class="field">
              <label for="confirm-password">Confirm Password <span class="required">*</span></label>
              <div class="field-password-input">
                <input
                  type="password"
                  id="confirm-password"
                  name="confirm-password"
                  placeholder="••••••••"
                  required
                  autocomplete="new-password"
                  minlength="8"
                />
              </div>
            </div>

            <div class="auth-error" id="error-message" hidden></div>

            <button type="submit" class="btn btn--primary btn--lg" id="register-btn">
              ${icons.check} Create account
            </button>
          </form>

          <div class="auth-footer">
            <p>Already have an account? <a href="#/login" class="auth-link">Sign in</a></p>
          </div>
        </div>
      </div>
    </div>
  `;

  const form = container.querySelector("#register-form");
  const nameInput = container.querySelector("#name");
  const emailInput = container.querySelector("#email");
  const passwordInput = container.querySelector("#password");
  const confirmPasswordInput = container.querySelector("#confirm-password");
  const registerBtn = container.querySelector("#register-btn");
  const errorMessage = container.querySelector("#error-message");

  // Form submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorMessage.hidden = true;
    registerBtn.disabled = true;
    registerBtn.classList.add("is-loading");

    try {
      const name = nameInput.value.trim();
      const email = emailInput.value.trim();
      const password = passwordInput.value;
      const confirmPassword = confirmPasswordInput.value;

      // Client-side validation
      if (!name) {
        throw new Error("Full name is required");
      }
      if (!email) {
        throw new Error("Email is required");
      }
      if (!password) {
        throw new Error("Password is required");
      }
      if (password.length < 8) {
        throw new Error("Password must be at least 8 characters");
      }
      if (password !== confirmPassword) {
        throw new Error("Passwords do not match");
      }

      const result = await api.register(name, email, password, confirmPassword);

      // Store token and update auth state
      store.setAuthToken(result.token);
      updateAuthState(result.user);
      updateAuthStateCache(result.user);
      mountNav();

      toast("Account created successfully!", { kind: "success" });
      navigate("/");
    } catch (err) {
      const message = err.friendly || err.message || "Registration failed. Please try again.";
      errorMessage.textContent = message;
      errorMessage.hidden = false;
      toast(message, { kind: "error" });
    } finally {
      registerBtn.disabled = false;
      registerBtn.classList.remove("is-loading");
    }
  });
}

