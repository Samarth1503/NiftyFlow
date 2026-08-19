"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Eye, EyeOff } from "lucide-react";

type Mode = "login" | "signup" | "forgot" | "reset";

export default function LoginPage() {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  
  const [showPassword, setShowPassword] = useState(false);
  
  const { login } = useAuth();

  useEffect(() => {
    // Parse URL for 1-click password reset token
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const m = params.get("mode");
      const t = params.get("token");
      if (m === "reset" && t) {
        setMode("reset");
        setResetToken(t);
        // Clear url without reloading
        window.history.replaceState({}, document.title, "/login");
      }
    }
  }, []);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMsg("");

    if ((mode === "signup" || mode === "reset") && password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    try {
      if (mode === "signup") {
        await api.post("/signup", { email, password });
        setMsg("Account created successfully. Please sign in.");
        setMode("login");
        setPassword("");
        setConfirmPassword("");
      } else if (mode === "login") {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const res = await api.post("/login/access-token", formData, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        });
        await login(res.data.access_token);
      } else if (mode === "forgot") {
        const res = await api.post("/password-recovery", { email });
        setMsg("Recovery link sent! Please check your email inbox to reset your password.");
        // We do not transition to "reset" mode here anymore. The user will click the link in their email.
      } else if (mode === "reset") {
        const res = await api.post("/reset-password", { token: resetToken, new_password: password });
        
        // Auto-login if backend returns an access_token seamlessly
        if (res.data.access_token) {
           await login(res.data.access_token);
        } else {
          setMsg("Password reset successfully. Please sign in.");
          setMode("login");
          setPassword("");
          setConfirmPassword("");
          setResetToken("");
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Action failed.");
    }
  };

  return (
    <div className="flex justify-center mt-20">
      <div className="bg-[var(--gf-surface)] p-8 rounded-xl border border-[var(--gf-border)] w-full max-w-md shadow-lg">
        <h2 className="text-2xl font-medium mb-6 text-center">
          {mode === "login" && "Sign in to NiftyFlow"}
          {mode === "signup" && "Create an Account"}
          {mode === "forgot" && "Reset Password"}
          {mode === "reset" && "Set New Password"}
        </h2>
        
        {error && <div className="bg-[var(--gf-red-bg)] text-[var(--gf-red)] p-3 rounded mb-4 text-sm">{error}</div>}
        {msg && <div className="bg-[var(--gf-green-bg)] text-[var(--gf-green)] p-3 rounded mb-4 text-sm">{msg}</div>}
        
        <form onSubmit={handleAuth} className="flex flex-col gap-4">
          {(mode === "login" || mode === "signup" || mode === "forgot") && (
            <div>
              <label className="block text-sm text-[var(--gf-gray-text)] mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[var(--background)] border border-[var(--gf-border)] rounded-lg p-2.5 text-white focus:outline-none focus:border-[var(--gf-blue)] transition-colors"
                required
              />
            </div>
          )}

          {mode === "reset" && (
            <div className="hidden">
              <label className="block text-sm text-[var(--gf-gray-text)] mb-1">Recovery Token</label>
              <input
                type="text"
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
                className="w-full bg-[var(--background)] border border-[var(--gf-border)] rounded-lg p-2.5 text-white focus:outline-none focus:border-[var(--gf-blue)] transition-colors"
              />
            </div>
          )}
          
          {(mode === "login" || mode === "signup" || mode === "reset") && (
            <div>
              <label className="block text-sm text-[var(--gf-gray-text)] mb-1">
                {mode === "reset" ? "New Password" : "Password"}
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[var(--background)] border border-[var(--gf-border)] rounded-lg p-2.5 pr-10 text-white focus:outline-none focus:border-[var(--gf-blue)] transition-colors"
                  required
                />
                <button 
                  type="button" 
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--gf-gray-text)] hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          )}

          {(mode === "signup" || mode === "reset") && (
            <div>
              <label className="block text-sm text-[var(--gf-gray-text)] mb-1">
                {mode === "reset" ? "Confirm New Password" : "Confirm Password"}
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-[var(--background)] border border-[var(--gf-border)] rounded-lg p-2.5 pr-10 text-white focus:outline-none focus:border-[var(--gf-blue)] transition-colors"
                  required
                />
                <button 
                  type="button" 
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--gf-gray-text)] hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          )}
          
          <button
            type="submit"
            className="mt-2 bg-[var(--gf-blue)] text-black font-medium py-2.5 rounded-lg hover:opacity-90 transition-opacity"
          >
            {mode === "login" && "Continue"}
            {mode === "signup" && "Sign Up"}
            {mode === "forgot" && "Send Reset Link"}
            {mode === "reset" && "Update Password"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-[var(--gf-gray-text)] flex flex-col gap-2">
          {mode === "login" && (
            <>
              <button onClick={() => { setMode("forgot"); setError(""); setMsg(""); }} className="hover:text-white transition-colors">Forgot your password?</button>
              <button onClick={() => { setMode("signup"); setError(""); setMsg(""); }} className="hover:text-white transition-colors">Don't have an account? Sign up</button>
            </>
          )}
          {mode !== "login" && (
            <button onClick={() => { setMode("login"); setError(""); setMsg(""); }} className="hover:text-white transition-colors">Back to Sign In</button>
          )}
        </div>
      </div>
    </div>
  );
}
