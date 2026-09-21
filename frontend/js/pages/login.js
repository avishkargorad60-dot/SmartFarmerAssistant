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
            <h2>Welcome back</h2>
            <p>Smarter insights. Better farming. Sign in to continue with your farm intelligence workspace.</p>
          </div>

          <form id="login-form" class="stack-form auth-form">
            <div class="field">
              <label for="email">Email</label>
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
              <div class="field-password-head">
                <label for="password">Password</label>
                <button type="button" class="btn-show-password" id="show-password-btn" aria-label="Show password">
                  ${icons.eye}
                </button>
              </div>
              <div class="field-password-input">
                <input
                  type="password"
                  id="password"
                  name="password"
                  placeholder="••••••••"
                  required
                  autocomplete="current-password"
                />
              </div>
            </div>

            <div class="auth-error" id="error-message" hidden></div>

            <button type="submit" class="btn btn--primary btn--lg" id="login-btn">
              ${icons.check} Sign in
            </button>
          </form>

          <div class="auth-footer">
            <p>Don't have an account? <a href="#/register" class="auth-link">Create one</a></p>
          </div>
        </div>
      </div>
    </div>
  `;

  const form = container.querySelector("#login-form");
  const emailInput = container.querySelector("#email");
  const passwordInput = container.querySelector("#password");
  const showPasswordBtn = container.querySelector("#show-password-btn");
  const loginBtn = container.querySelector("#login-btn");
  const errorMessage = container.querySelector("#error-message");

  // Show/hide password
  showPasswordBtn.addEventListener("click", (e) => {
    e.preventDefault();
    const isPassword = passwordInput.type === "password";
    passwordInput.type = isPassword ? "text" : "password";
    showPasswordBtn.innerHTML = isPassword ? icons.eyeOff : icons.eye;
    showPasswordBtn.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
  });

  // Form submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorMessage.hidden = true;
    loginBtn.disabled = true;
    loginBtn.classList.add("is-loading");

    try {
      const email = emailInput.value.trim();
      const password = passwordInput.value;

      if (!email || !password) {
        throw new Error("Email and password are required");
      }

      const result = await api.login(email, password);

      // Store token and update auth state
      store.setAuthToken(result.token);
      updateAuthState(result.user);
      updateAuthStateCache(result.user);
      mountNav();

      toast("Signed in successfully!", { kind: "success" });
      navigate("/");
    } catch (err) {
      const message = err.friendly || err.message || "Sign in failed. Please try again.";
      errorMessage.textContent = message;
      errorMessage.hidden = false;
      toast(message, { kind: "error" });
    } finally {
      loginBtn.disabled = false;
      loginBtn.classList.remove("is-loading");
    }
  });
}

