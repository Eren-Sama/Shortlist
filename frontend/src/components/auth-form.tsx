"use client";

import { useState, type FormEvent } from "react";
import { useAuth } from "@/components/auth-provider";

export function AuthForm() {
  const { signInWithEmail, signUpWithEmail, signInWithGoogle } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (isSignUp && password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      if (isSignUp) {
        await signUpWithEmail(email, password);
        setSuccess("Check your email for a confirmation link.");
      } else {
        await signInWithEmail(email, password);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError(null);
    setGoogleLoading(true);
    try {
      await signInWithGoogle();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Google sign-in failed");
      setGoogleLoading(false);
    }
  };

  return (
    <div className="w-full max-w-sm space-y-6 animate-reveal d3">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-primary">
          {isSignUp ? "Create account" : "Sign in"}
        </h2>
        <p className="mt-1 text-sm text-secondary">
          {isSignUp
            ? "Start building your portfolio"
            : "Welcome back to Shortlist"}
        </p>
      </div>

      {/* Google OAuth */}
      <button
        type="button"
        onClick={handleGoogleSignIn}
        disabled={googleLoading}
        className="flex w-full items-center justify-center gap-3 rounded-lg border border-edge bg-surface px-4 py-2.5 text-sm font-medium text-primary transition hover:bg-raised hover:border-edge-strong disabled:opacity-40"
      >
        <svg className="h-4.5 w-4.5" viewBox="0 0 24 24">
          <path
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
            fill="#4285F4"
          />
          <path
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            fill="#34A853"
          />
          <path
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            fill="#FBBC05"
          />
          <path
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            fill="#EA4335"
          />
        </svg>
        {googleLoading ? "Redirecting..." : "Continue with Google"}
      </button>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-edge" />
        </div>
        <div className="relative flex justify-center text-[11px] uppercase tracking-wider">
          <span className="bg-surface px-3 text-muted">or</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="email"
            className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg px-4 py-2.5 text-sm"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label
            htmlFor="password"
            className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg px-4 py-2.5 text-sm"
            placeholder="••••••••"
          />
        </div>

        {isSignUp && (
          <div>
            <label
              htmlFor="confirmPassword"
              className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted"
            >
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              required
              minLength={6}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-lg px-4 py-2.5 text-sm"
              placeholder="••••••••"
            />
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-danger/30 bg-danger-dim px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        {success && (
          <div className="rounded-lg border border-ok/30 bg-ok-dim px-4 py-3 text-sm text-ok">
            {success}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-root transition hover:bg-accent-hover disabled:opacity-40"
        >
          {loading
            ? "Loading..."
            : isSignUp
              ? "Create Account"
              : "Sign In"}
        </button>
      </form>

      <div className="text-center">
        <button
          onClick={() => {
            setIsSignUp(!isSignUp);
            setError(null);
            setSuccess(null);
            setConfirmPassword("");
          }}
          className="text-sm text-muted transition hover:text-primary"
        >
          {isSignUp
            ? "Already have an account? Sign in"
            : "Don't have an account? Sign up"}
        </button>
      </div>
    </div>
  );
}
