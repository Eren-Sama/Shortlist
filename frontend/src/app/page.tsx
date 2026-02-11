"use client";

import { useRef, useEffect, useState, type ReactNode, useCallback } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useInView,
  useMotionValue,
  useMotionTemplate,
  useSpring,
  animate,
  AnimatePresence,
} from "framer-motion";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import { AuthForm } from "@/components/auth-form";
import { SmoothScrollProvider } from "@/components/landing/smooth-scroll";
import DarkVeil from "@/components/landing/DarkVeil";
import { ArrowRight, ArrowUpRight, X } from "lucide-react";

// Motion
const ease = [0.16, 1, 0.3, 1] as const;

// Animated counter
function Counter({ to, suffix = "" }: { to: number; suffix?: string }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const val = useMotionValue(0);
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!inView) return;
    const ctrl = animate(val, to, {
      duration: 2,
      ease,
      onUpdate: (v) => setN(Math.round(v)),
    });
    return ctrl.stop;
  }, [inView, to, val]);
  return (
    <span ref={ref} className="tabular-nums">
      {n}
      {suffix}
    </span>
  );
}

// Spotlight card (cursor-reactive)
function SpotlightCard({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const sx = useSpring(mx, { damping: 25, stiffness: 150 });
  const sy = useSpring(my, { damping: 25, stiffness: 150 });
  const bg = useMotionTemplate`radial-gradient(500px circle at ${sx}px ${sy}px, rgba(200,255,0,0.045), transparent 60%)`;

  const move = useCallback(
    (e: React.MouseEvent) => {
      if (!ref.current) return;
      const r = ref.current.getBoundingClientRect();
      mx.set(e.clientX - r.left);
      my.set(e.clientY - r.top);
    },
    [mx, my]
  );

  return (
    <motion.div
      ref={ref}
      onMouseMove={move}
      className={`gradient-border glass group relative overflow-hidden ${className}`}
    >
      <motion.div
        className="pointer-events-none absolute inset-0 z-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100"
        style={{ background: bg }}
      />
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}

// Marquee
function Marquee({ children }: { children: ReactNode }) {
  return (
    <div className="relative overflow-hidden select-none">
      <div className="pointer-events-none absolute left-0 top-0 z-10 h-full w-32 bg-gradient-to-r from-root to-transparent" />
      <div className="pointer-events-none absolute right-0 top-0 z-10 h-full w-32 bg-gradient-to-l from-root to-transparent" />
      <div className="animate-marquee flex w-max items-center gap-20">
        {children}
        {children}
      </div>
    </div>
  );
}

// PAGE
export default function HomePage() {
  const { user, loading } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [showAuth, setShowAuth] = useState(false);

  const { scrollY } = useScroll();
  const heroY = useTransform(scrollY, [0, 900], ["0%", "40%"]);
  const heroOp = useTransform(scrollY, [0, 600], [1, 0]);
  const heroScale = useTransform(scrollY, [0, 700], [1, 0.92]);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", fn, { passive: true });
    return () => window.removeEventListener("scroll", fn);
  }, []);

  useEffect(() => {
    if (user) setShowAuth(false);
  }, [user]);

  if (loading)
    return (
      <div className="flex min-h-screen items-center justify-center bg-root">
        <div className="h-7 w-7 rounded-full border-2 border-accent border-t-transparent animate-spin" />
      </div>
    );

  return (
    <SmoothScrollProvider>
      {/* grain */}
      <div className="noise-overlay fixed inset-0 pointer-events-none z-50 opacity-[0.015]" />

      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease }}
        className="fixed inset-x-0 top-5 z-40 mx-auto max-w-7xl px-4"
      >
        <nav className={`relative flex items-center justify-between rounded-[18px] px-7 py-3 md:px-10 transition-all duration-700 ${
          scrolled
            ? "bg-root/70 backdrop-blur-3xl shadow-[0_8px_40px_rgba(0,0,0,0.55),inset_0_1px_0_rgba(255,255,255,0.05)]"
            : "bg-white/[0.025] backdrop-blur-2xl shadow-[0_4px_30px_rgba(0,0,0,0.25),inset_0_1px_0_rgba(255,255,255,0.04)]"
        }`}>
          {/* Gradient border overlay */}
          <div className="pointer-events-none absolute inset-0 rounded-[18px] border border-white/[0.07]" />
          <div className="pointer-events-none absolute inset-0 rounded-[18px] bg-gradient-to-r from-accent/[0.05] via-transparent to-accent/[0.05] opacity-0 transition-opacity duration-700" style={{ opacity: scrolled ? 1 : 0 }} />

          <Link href="/" className="group relative z-10 flex items-center gap-2.5">
            <div className="relative h-3 w-3">
              <div className="absolute inset-0 rounded-[3px] bg-accent" />
              <div className="absolute inset-0 rounded-[3px] bg-accent blur-[8px] opacity-50 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
            <span className="text-[13px] font-bold tracking-[0.22em] uppercase text-primary/90 group-hover:text-primary transition-colors duration-300">
              Shortlist
            </span>
          </Link>

          <div className="relative z-10 hidden md:flex items-center gap-1.5">
            {["Features", "Process", "Metrics"].map((l) => (
              <a
                key={l}
                href={`#${l.toLowerCase()}`}
                className="relative rounded-lg px-4 py-2 text-[11px] font-semibold text-white/45 hover:text-white/95 hover:bg-white/[0.05] transition-all duration-300 tracking-widest uppercase"
              >
                {l}
              </a>
            ))}
          </div>

          <div className="relative z-10 flex items-center gap-3 sm:gap-4">
            {user ? (
              <Link
                href="/dashboard"
                className="group flex items-center gap-2 rounded-full bg-accent px-5 py-2 text-[12px] font-bold text-root tracking-wide hover:shadow-[0_0_40px_rgba(200,255,0,0.35)] hover:scale-[1.02] transition-all duration-300"
              >
                Dashboard
                <ArrowRight className="h-3.5 w-3.5 transition-transform duration-300 group-hover:translate-x-0.5" />
              </Link>
            ) : (
              <>
                <button
                  onClick={() => setShowAuth(true)}
                  className="hidden sm:inline-flex rounded-full border border-white/[0.12] bg-white/[0.04] px-5 py-2 text-[12px] font-semibold text-primary/80 hover:text-primary hover:bg-white/[0.08] hover:border-white/[0.2] transition-all duration-300"
                >
                  Sign in
                </button>
                <button
                  onClick={() => setShowAuth(true)}
                  className="group flex items-center gap-2 rounded-full bg-accent px-4 sm:px-5 py-2 text-[11px] sm:text-[12px] font-bold text-root tracking-wide hover:shadow-[0_0_40px_rgba(200,255,0,0.35)] hover:scale-[1.02] transition-all duration-300"
                >
                  Get started
                  <ArrowRight className="h-3.5 w-3.5 transition-transform duration-300 group-hover:translate-x-0.5" />
                </button>
              </>
            )}
          </div>
        </nav>
      </motion.header>

      <AnimatePresence>
        {showAuth && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-2xl"
            onClick={() => setShowAuth(false)}
          >
            <motion.div
              initial={{ opacity: 0, y: 50, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 50, scale: 0.9 }}
              transition={{ duration: 0.45, ease }}
              onClick={(e) => e.stopPropagation()}
              className="relative w-full max-w-sm mx-4"
            >
              {/* glow ring */}
              <div className="absolute -inset-px rounded-2xl bg-gradient-to-b from-accent/20 via-accent/5 to-transparent" />
              <div className="relative rounded-2xl bg-surface border border-edge p-8">
                <button
                  onClick={() => setShowAuth(false)}
                  className="absolute right-4 top-4 rounded-lg p-1 text-muted hover:text-primary transition"
                >
                  <X className="h-4 w-4" />
                </button>
                <AuthForm />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* HERO */}
      <section className="relative flex min-h-[105vh] items-center overflow-hidden">
        <div className="absolute inset-0 overflow-hidden bg-black">
          <DarkVeil
            hueShift={80}
            speed={0.4}
            noiseIntensity={0}
            scanlineIntensity={0}
            scanlineFrequency={0}
            warpAmount={0}
            resolutionScale={1}
          />
          {/* Deep dark falloff — lower half stays pitch black */}
          <div className="absolute bottom-0 inset-x-0 h-[55%]" style={{ background: 'linear-gradient(to top, #08080a 0%, rgba(8,8,10,0.95) 40%, transparent 100%)' }} />
        </div>

        {/* Fine grid overlay */}
        <div className="absolute inset-0 grid-pattern opacity-15" />

        {/* Radial vignette — heavy to keep bottom pitch black */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_25%,transparent_20%,#000000_75%)]" />

        {/* Content */}
        <motion.div
          style={{ y: heroY, opacity: heroOp, scale: heroScale }}
          className="relative z-10 mx-auto w-full max-w-7xl px-6 md:px-10 pt-32 pb-20"
        >
          <motion.div
            initial="h"
            animate="v"
            variants={{ h: {}, v: { transition: { staggerChildren: 0.1 } } }}
            className="flex flex-col items-center text-center"
          >
            {/* Badge */}
            {/* Headline */}
            {["Build portfolios", "that get you", "hired."].map((line, i) => (
              <motion.h1
                key={i}
                variants={{
                  h: { opacity: 0, y: 70, rotateX: -20, filter: "blur(12px)" },
                  v: {
                    opacity: 1,
                    y: 0,
                    rotateX: 0,
                    filter: "blur(0px)",
                    transition: { duration: 1.2, ease },
                  },
                }}
                className={`text-[clamp(3rem,9vw,7.5rem)] font-bold leading-[0.95] tracking-[-0.03em] ${
                  i === 2
                    ? "bg-gradient-to-r from-accent via-[#e8ff66] to-accent animate-gradient-text"
                    : "text-primary"
                }`}
                style={i === 2 ? { perspective: 800 } : undefined}
              >
                {line}
              </motion.h1>
            ))}

            {/* Sub */}
            <motion.p
              variants={{
                h: { opacity: 0, y: 30, filter: "blur(8px)" },
                v: {
                  opacity: 1,
                  y: 0,
                  filter: "blur(0px)",
                  transition: { duration: 0.9, ease },
                },
              }}
              className="mt-8 max-w-xl text-lg leading-relaxed text-secondary/80 md:text-xl"
            >
              Analyzes job descriptions, scores your repos, generates capstone
              projects, and crafts recruiter-ready assets — powered by AI.
            </motion.p>

            {/* CTAs */}
            <motion.div
              variants={{
                h: { opacity: 0, y: 25 },
                v: { opacity: 1, y: 0, transition: { duration: 0.8, ease } },
              }}
              className="mt-10 flex flex-wrap justify-center gap-4"
            >
              {user ? (
                <Link
                  href="/dashboard"
                  className="group relative inline-flex items-center gap-2.5 rounded-full bg-accent px-8 py-3.5 text-sm font-bold text-root transition-all hover:shadow-[0_0_50px_rgba(200,255,0,0.35)]"
                >
                  <span>Go to Dashboard</span>
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
              ) : (
                <button
                  onClick={() => setShowAuth(true)}
                  className="group relative overflow-hidden inline-flex items-center gap-2.5 rounded-full bg-accent px-8 py-3.5 text-sm font-bold text-root transition-all hover:shadow-[0_0_50px_rgba(200,255,0,0.35)]"
                >
                  {/* shimmer beam */}
                  <span className="absolute inset-0 beam" />
                  <span className="relative">Start for free</span>
                  <ArrowRight className="relative h-4 w-4 transition-transform group-hover:translate-x-1" />
                </button>
              )}
              <a
                href="#features"
                className="group inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.02] px-7 py-3.5 text-sm text-secondary backdrop-blur-sm transition-all hover:border-white/[0.15] hover:text-primary"
              >
                Explore features
                <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </a>
            </motion.div>

            {/* Tech strip */}
            <motion.div
              variants={{
                h: { opacity: 0 },
                v: { opacity: 1, transition: { duration: 1, delay: 0.6, ease } },
              }}
              className="mt-16 flex flex-wrap justify-center gap-x-6 gap-y-2"
            >
              {["FastAPI", "Next.js", "Groq AI", "Supabase", "TypeScript"].map(
                (t) => (
                  <span
                    key={t}
                    className="text-[11px] font-mono text-muted/50 tracking-wide"
                  >
                    {t}
                  </span>
                )
              )}
            </motion.div>
          </motion.div>
        </motion.div>

        {/* bottom fade */}
        <div className="absolute bottom-0 inset-x-0 h-48 bg-gradient-to-t from-root via-root/80 to-transparent" />
      </section>

      <section className="relative py-20 overflow-hidden">
        {/* Intense neon top/bottom glow lines */}
        <div className="absolute top-0 inset-x-0">
          <div className="h-px bg-gradient-to-r from-transparent via-accent/60 to-transparent" />
          <div className="h-[8px] bg-gradient-to-r from-transparent via-accent/[0.12] to-transparent blur-[6px]" />
        </div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ margin: "-40px" }}
          transition={{ duration: 0.7, ease }}
        >
          <p className="mb-12 text-center text-[13px] sm:text-[15px] font-bold uppercase tracking-[0.3em] sm:tracking-[0.4em] text-muted/80">
            Engineers targeting these companies use Shortlist
          </p>
          <Marquee>
            {/* Tech company logos — clean text wordmarks + verified icon SVGs */}
            {[
              /* Google — text wordmark */
              <span key="google" className="text-[22px] font-medium tracking-tight text-[#a0a0aa] opacity-30 hover:opacity-60 transition-opacity duration-300 select-none" style={{ fontFamily: "'Product Sans', 'Google Sans', sans-serif" }}>Google</span>,
              /* Apple — verified icon */
              <svg key="apple" className="h-6 opacity-30 hover:opacity-60 transition-opacity duration-300" viewBox="0 0 814 1000" fill="#a0a0aa"><path d="M788.1 340.9c-5.8 4.5-108.2 62.2-108.2 190.5 0 148.4 130.3 200.9 134.2 202.2-.6 3.2-20.7 71.9-68.7 141.9-42.8 61.6-87.5 123.1-155.5 123.1s-85.5-39.5-164-39.5c-76.5 0-103.7 40.8-165.9 40.8s-105.6-57.8-155.5-127.4c-58.1-82-102-205.8-102-324.8 0-191 124.1-292.6 246.2-292.6 65 0 119.1 42.8 159.7 42.8 38.9 0 99.3-45.2 173.9-45.2 28.1 0 129 2.6 195.8 97.2zm-282.3-89.8c31.2-37 53.5-88.2 53.5-139.4 0-7.1-.6-14.3-1.9-20.1-51 1.9-110.7 33.9-147 75.8-28.7 32.5-55.8 83.8-55.8 135.7 0 7.8.6 15.6 1.3 18.2 2.6.6 6.4 1.3 10.8 1.3 45.8 0 103.2-30.4 139.1-71.5z"/></svg>,
              /* Vercel — triangle icon + text */
              <span key="vercel" className="inline-flex items-center gap-1.5 opacity-30 hover:opacity-60 transition-opacity duration-300 select-none">
                <svg className="h-4" viewBox="0 0 76 65" fill="#a0a0aa"><path d="M37.5 0L75 65H0L37.5 0z"/></svg>
                <span className="text-[18px] font-semibold tracking-tight text-[#a0a0aa]">Vercel</span>
              </span>,
              /* Meta — text wordmark */
              <span key="meta" className="text-[22px] font-bold tracking-tight text-[#a0a0aa] opacity-30 hover:opacity-60 transition-opacity duration-300 select-none">Meta</span>,
              /* Stripe — text wordmark */
              <span key="stripe" className="text-[24px] font-bold tracking-tight text-[#a0a0aa] opacity-30 hover:opacity-60 transition-opacity duration-300 select-none italic">stripe</span>,
              /* Netflix — text wordmark */
              <span key="netflix" className="text-[22px] font-bold tracking-widest text-[#a0a0aa] opacity-30 hover:opacity-60 transition-opacity duration-300 select-none uppercase">Netflix</span>,
              /* Linear — verified icon */
              <span key="linear" className="inline-flex items-center gap-1.5 opacity-30 hover:opacity-60 transition-opacity duration-300 select-none">
                <svg className="h-5" viewBox="0 0 100 100" fill="#a0a0aa"><path d="M1.22 61.5a48.5 48.5 0 0 0 37.28 37.28L1.22 61.5zm-1-7.63a49.83 49.83 0 0 0 3.37 13.77L46.64 24.6A49.83 49.83 0 0 0 32.87.22L.22 53.87zM15.4 85.6a49 49 0 0 0 6.84 6.16L85.76 28.24a49 49 0 0 0-6.16-6.84L15.4 85.6zM29.58 95.4a49.29 49.29 0 0 0 9.32 3.6L98.9 39C97.87 35.73 96.5 32.6 94.8 29.62L29.58 95.4zM46.8 99.87a49.48 49.48 0 0 0 52.33-52.33L46.8 99.87zM50 .13a49.48 49.48 0 0 0-9.23 1 49.52 49.52 0 0 0-4.34 1.32l62.12 62.12a49.52 49.52 0 0 0 1.32-4.34 49.48 49.48 0 0 0 1-9.23C100.87 22.81 77.19.13 50 .13z"/></svg>
                <span className="text-[18px] font-semibold tracking-tight text-[#a0a0aa]">Linear</span>
              </span>,
              /* Figma — verified icon */
              <span key="figma" className="inline-flex items-center gap-1.5 opacity-30 hover:opacity-60 transition-opacity duration-300 select-none">
                <svg className="h-5" viewBox="0 0 38 57" fill="#a0a0aa"><path d="M19 28.5a9.5 9.5 0 1 1 19 0 9.5 9.5 0 0 1-19 0z"/><path d="M0 47.5A9.5 9.5 0 0 1 9.5 38H19v9.5a9.5 9.5 0 1 1-19 0z"/><path d="M19 0v19h9.5a9.5 9.5 0 1 0 0-19H19z"/><path d="M0 9.5A9.5 9.5 0 0 0 9.5 19H19V0H9.5A9.5 9.5 0 0 0 0 9.5z"/><path d="M0 28.5A9.5 9.5 0 0 0 9.5 38H19V19H9.5A9.5 9.5 0 0 0 0 28.5z"/></svg>
                <span className="text-[18px] font-semibold tracking-tight text-[#a0a0aa]">Figma</span>
              </span>,
              /* Shopify — text wordmark */
              <span key="shopify" className="text-[22px] font-bold tracking-tight text-[#a0a0aa] opacity-30 hover:opacity-60 transition-opacity duration-300 select-none">Shopify</span>,
              /* Airbnb — text wordmark */
              <span key="airbnb" className="text-[22px] font-bold tracking-tight text-[#a0a0aa] opacity-30 hover:opacity-60 transition-opacity duration-300 select-none">airbnb</span>,
              /* Notion — text wordmark */
              <span key="notion" className="text-[22px] font-bold tracking-tight text-[#a0a0aa] opacity-30 hover:opacity-60 transition-opacity duration-300 select-none">Notion</span>,
              /* GitHub — verified icon + text */
              <span key="github" className="inline-flex items-center gap-1.5 opacity-30 hover:opacity-60 transition-opacity duration-300 select-none">
                <svg className="h-5" viewBox="0 0 98 96" fill="#a0a0aa"><path fillRule="evenodd" clipRule="evenodd" d="M48.85 0C21.84 0 0 22 0 49.22c0 21.76 14.07 40.2 33.58 46.74 2.46.46 3.36-1.07 3.36-2.38 0-1.17-.04-4.28-.07-8.41-13.66 2.97-16.54-6.59-16.54-6.59-2.24-5.68-5.46-7.2-5.46-7.2-4.47-3.05.34-2.99.34-2.99 4.94.35 7.53 5.07 7.53 5.07 4.39 7.52 11.5 5.35 14.3 4.09.45-3.18 1.72-5.35 3.13-6.58-10.9-1.24-22.37-5.46-22.37-24.27 0-5.36 1.91-9.74 5.05-13.18-.5-1.24-2.19-6.24.48-13 0 0 4.12-1.32 13.5 5.03 3.91-1.09 8.11-1.63 12.28-1.65 4.17.02 8.37.56 12.29 1.65 9.36-6.35 13.47-5.03 13.47-5.03 2.68 6.76 1 11.76.5 13 3.14 3.44 5.04 7.82 5.04 13.18 0 18.86-11.49 23.01-22.43 24.22 1.76 1.52 3.33 4.51 3.33 9.1 0 6.57-.06 11.86-.06 13.47 0 1.31.88 2.85 3.38 2.37C84.79 89.4 98.84 70.96 98.84 49.22 98.84 22 76.86 0 48.85 0z"/></svg>
                <span className="text-[18px] font-semibold tracking-tight text-[#a0a0aa]">GitHub</span>
              </span>,
            ].map((logo, i) => (
              <span key={i} className="inline-flex items-center shrink-0 px-2">
                {logo}
              </span>
            ))}
          </Marquee>
        </motion.div>
      </section>

      <div className="glow-line mx-auto max-w-5xl" />

      {/* FEATURES — BENTO */}
      <section id="features" className="relative px-6 md:px-10 py-32">
        <div className="mx-auto max-w-7xl">
          {/* heading */}
          <motion.div
            initial={{ opacity: 0, y: 40, filter: "blur(8px)" }}
            whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            viewport={{ margin: "-80px" }}
            transition={{ duration: 0.9, ease }}
            className="mb-20 max-w-2xl"
          >
            <span className="text-[11px] font-bold uppercase tracking-[0.3em] text-accent/80">
              Features
            </span>
            <h2 className="mt-4 text-4xl font-bold tracking-tight md:text-5xl lg:text-6xl">
              Four engines,{" "}
              <span className="bg-gradient-to-r from-accent to-[#80ffb0] animate-gradient-text">
                one pipeline.
              </span>
            </h2>
            <p className="mt-5 text-lg text-secondary/70 max-w-lg leading-relaxed">
              From job listing to recruiter-ready portfolio — every step automated,
              every output optimized.
            </p>
          </motion.div>

          {/* cards */}
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {/* Card 1 — JD Analyzer (wide) */}
            <motion.div
              initial={{ opacity: 0, y: 50, filter: "blur(8px)" }}
              whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              viewport={{ margin: "-60px" }}
              transition={{ duration: 0.9, ease }}
              className="lg:col-span-2"
            >
              <SpotlightCard className="h-full p-8 md:p-10">
                <div className="flex flex-col gap-6 md:flex-row md:items-start md:gap-10">
                  <div className="shrink-0">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-accent/25 to-accent/8 shadow-[0_0_40px_rgba(200,255,0,0.15),inset_0_1px_0_rgba(200,255,0,0.1)]">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-accent">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>
                        <path d="M2 12h20"/>
                      </svg>
                    </div>
                    <div className="mt-3 h-px w-12 bg-gradient-to-r from-accent/30 to-transparent" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent/60 mb-2 block">Core Engine</span>
                    <h3 className="text-xl font-bold text-primary mb-3">JD Analyzer</h3>
                    <p className="text-[15px] leading-relaxed text-secondary/70">
                      Paste any job description — our AI extracts skills, experience
                      levels, company signals, and engineering expectations with
                      weighted priorities. Maps role DNA in seconds.
                    </p>
                  </div>
                </div>
              </SpotlightCard>
            </motion.div>

            {/* Card 2 — Repo Scorer */}
            <motion.div
              initial={{ opacity: 0, y: 50, filter: "blur(8px)" }}
              whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              viewport={{ margin: "-60px" }}
              transition={{ duration: 0.9, delay: 0.08, ease }}
            >
              <SpotlightCard className="h-full p-8 md:p-10">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#60a5fa]/20 to-[#60a5fa]/5">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-info">
                    <line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/>
                    <path d="M18 9a9 9 0 0 1-9 9"/>
                  </svg>
                </div>
                <div className="mt-3 h-px w-12 bg-gradient-to-r from-info/30 to-transparent" />
                <span className="mt-4 text-[10px] font-bold uppercase tracking-[0.2em] text-info/60 block">15+ Dimensions</span>
                <h3 className="mt-2 text-xl font-bold text-primary">Repo Scorer</h3>
                <p className="mt-3 text-[15px] leading-relaxed text-secondary/70">
                  Recruiter-focused scorecards for any GitHub repo. Code quality,
                  tests, complexity, structure — all quantified out of 10.
                </p>
              </SpotlightCard>
            </motion.div>

            {/* Card 3 — Scaffold Generator */}
            <motion.div
              initial={{ opacity: 0, y: 50, filter: "blur(8px)" }}
              whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              viewport={{ margin: "-60px" }}
              transition={{ duration: 0.9, delay: 0.16, ease }}
            >
              <SpotlightCard className="h-full p-8 md:p-10">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#fbbf24]/20 to-[#fbbf24]/5">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-warn">
                    <path d="M3 3h7v7H3z"/><path d="M14 3h7v7h-7z"/><path d="M14 14h7v7h-7z"/><path d="M3 14h7v7H3z"/>
                  </svg>
                </div>
                <div className="mt-3 h-px w-12 bg-gradient-to-r from-warn/30 to-transparent" />
                <span className="mt-4 text-[10px] font-bold uppercase tracking-[0.2em] text-warn/60 block">Auto-Generated</span>
                <h3 className="mt-2 text-xl font-bold text-primary">Scaffold Generator</h3>
                <p className="mt-3 text-[15px] leading-relaxed text-secondary/70">
                  Production-ready project structures with Docker, CI/CD, tests,
                  and architecture decisions — tailored to your stack.
                </p>
              </SpotlightCard>
            </motion.div>

            {/* Card 4 — Portfolio Optimizer (wide) */}
            <motion.div
              initial={{ opacity: 0, y: 50, filter: "blur(8px)" }}
              whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              viewport={{ margin: "-60px" }}
              transition={{ duration: 0.9, delay: 0.24, ease }}
              className="lg:col-span-2"
            >
              <SpotlightCard className="h-full p-8 md:p-10">
                <div className="flex flex-col gap-6 md:flex-row md:items-start md:gap-10">
                  <div className="shrink-0">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#c084fc]/20 to-[#c084fc]/5">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#c084fc]">
                        <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
                      </svg>
                    </div>
                    <div className="mt-3 h-px w-12 bg-gradient-to-r from-[#c084fc]/30 to-transparent" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#c084fc]/60 mb-2 block">Multi-Format</span>
                    <h3 className="text-xl font-bold text-primary mb-3">Portfolio Optimizer</h3>
                    <p className="text-[15px] leading-relaxed text-secondary/70">
                      Crafts polished README files, ATS-optimized resume bullets,
                      demo scripts, and LinkedIn posts — everything a recruiter
                      wants to see, packaged and ready to ship.
                    </p>
                  </div>
                </div>
              </SpotlightCard>
            </motion.div>
          </div>
        </div>
      </section>

      <div className="glow-line mx-auto max-w-5xl" />

      {/* PROCESS */}
      <section id="process" className="relative px-6 md:px-10 py-32">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-20 lg:grid-cols-2 lg:gap-32">
            {/* Left heading */}
            <motion.div
              initial={{ opacity: 0, x: -40, filter: "blur(8px)" }}
              whileInView={{ opacity: 1, x: 0, filter: "blur(0px)" }}
              viewport={{ margin: "-80px" }}
              transition={{ duration: 0.9, ease }}
              className="lg:sticky lg:top-32 lg:self-start"
            >
              <span className="text-[11px] font-bold uppercase tracking-[0.3em] text-accent/80">
                Process
              </span>
              <h2 className="mt-4 text-4xl font-bold tracking-tight md:text-5xl lg:text-6xl">
                JD to portfolio
                <br />
                in{" "}
                <span className="bg-gradient-to-r from-accent to-[#80ffb0] animate-gradient-text">
                  minutes.
                </span>
              </h2>
              <p className="mt-5 text-lg text-secondary/70 max-w-md leading-relaxed">
                Four steps. Zero guesswork. Every output tailored to the exact
                role you&apos;re targeting.
              </p>

              {/* mini flow */}
              <div className="mt-10 flex items-center gap-3">
                {[
                  { n: "01", color: "bg-accent/10 border-accent/15 text-accent" },
                  { n: "02", color: "bg-info/10 border-info/15 text-info" },
                  { n: "03", color: "bg-warn/10 border-warn/15 text-warn" },
                  { n: "04", color: "bg-[#c084fc]/10 border-[#c084fc]/15 text-[#c084fc]" },
                ].map((s, i) => (
                  <div key={s.n} className="flex items-center gap-3">
                    <div className={`h-10 w-10 rounded-xl flex items-center justify-center font-mono text-xs font-bold border shadow-[0_0_20px_rgba(200,255,0,0.04)] ${s.color}`}>
                      {s.n}
                    </div>
                    {i < 3 && <div className="h-px w-6 bg-gradient-to-r from-accent/30 via-accent/10 to-transparent" />}
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Right steps — premium glass cards */}
            <div className="relative space-y-5">

              {([
                {
                  n: "01",
                  title: "Paste",
                  desc: "Drop any job description — the AI parses role, skills, company type, seniority, and geography in real time.",
                  icon: (
                    <svg className="h-4.5 w-4.5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="2" width="14" height="16" rx="2" />
                      <path d="M7 2V4H13V2" />
                      <path d="M7 9H13M7 12H11" />
                    </svg>
                  ),
                  nodeBg: "bg-accent/10",
                  nodeBorder: "border-accent/20",
                  nodeText: "text-accent",
                  cardGlow: "hover:shadow-[0_0_40px_rgba(200,255,0,0.06)]",
                  accentBar: "from-accent/60 to-accent/0",
                  iconGlow: "group-hover:shadow-[0_0_24px_rgba(200,255,0,0.3)]",
                },
                {
                  n: "02",
                  title: "Analyze",
                  desc: "Weighted skill profiles, engineering expectations, and company-intelligence modifiers are extracted and scored.",
                  icon: (
                    <svg className="h-4.5 w-4.5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="10" cy="10" r="7" />
                      <path d="M10 6V10L13 13" />
                    </svg>
                  ),
                  nodeBg: "bg-info/10",
                  nodeBorder: "border-info/20",
                  nodeText: "text-info",
                  cardGlow: "hover:shadow-[0_0_40px_rgba(96,165,250,0.06)]",
                  accentBar: "from-info/60 to-info/0",
                  iconGlow: "group-hover:shadow-[0_0_24px_rgba(96,165,250,0.3)]",
                },
                {
                  n: "03",
                  title: "Build",
                  desc: "Capstone projects, production scaffolds, and architecture decisions — all generated for your target stack.",
                  icon: (
                    <svg className="h-4.5 w-4.5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 10L10 3L17 10" />
                      <path d="M5 8.5V16H8V12H12V16H15V8.5" />
                    </svg>
                  ),
                  nodeBg: "bg-warn/10",
                  nodeBorder: "border-warn/20",
                  nodeText: "text-warn",
                  cardGlow: "hover:shadow-[0_0_40px_rgba(251,191,36,0.06)]",
                  accentBar: "from-warn/60 to-warn/0",
                  iconGlow: "group-hover:shadow-[0_0_24px_rgba(251,191,36,0.3)]",
                },
                {
                  n: "04",
                  title: "Ship",
                  desc: "Polished README, ATS resume bullets, demo scripts, LinkedIn posts — ready to deploy, ready to impress.",
                  icon: (
                    <svg className="h-4.5 w-4.5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M10 2L18 7V13L10 18L2 13V7L10 2Z" />
                      <path d="M10 18V10" />
                      <path d="M18 7L10 12L2 7" />
                    </svg>
                  ),
                  nodeBg: "bg-[#c084fc]/10",
                  nodeBorder: "border-[#c084fc]/20",
                  nodeText: "text-[#c084fc]",
                  cardGlow: "hover:shadow-[0_0_40px_rgba(192,132,252,0.06)]",
                  accentBar: "from-[#c084fc]/60 to-[#c084fc]/0",
                  iconGlow: "group-hover:shadow-[0_0_24px_rgba(192,132,252,0.3)]",
                },
              ] as const).map((step, i) => (
                <motion.div
                  key={step.n}
                  initial={{ opacity: 0, x: 30, filter: "blur(6px)" }}
                  whileInView={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                  viewport={{ margin: "-60px" }}
                  transition={{ duration: 0.7, delay: i * 0.1, ease }}
                  className={`group relative flex items-start gap-5 rounded-2xl border border-white/[0.04] bg-white/[0.015] backdrop-blur-sm p-6 md:p-7 transition-all duration-500 hover:bg-white/[0.03] hover:border-white/[0.08] ${step.cardGlow}`}
                >
                  {/* Left accent bar */}
                  <div className={`pointer-events-none absolute left-0 top-5 bottom-5 w-[2px] rounded-full bg-gradient-to-b ${step.accentBar} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

                  {/* Step icon node */}
                  <div className="relative z-10 flex h-[54px] w-[54px] shrink-0 items-center justify-center">
                    <div className={`absolute inset-0 rounded-2xl ${step.nodeBg} border ${step.nodeBorder} transition-all duration-500 ${step.iconGlow}`} />
                    <span className={`relative ${step.nodeText} opacity-80`}>{step.icon}</span>
                  </div>

                  <div className="pt-1.5 min-w-0">
                    <h3 className={`text-lg font-bold tracking-tight ${step.nodeText}`}>{step.title}</h3>
                    <p className="mt-2 text-[13.5px] leading-relaxed text-secondary/55">
                      {step.desc}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="glow-line mx-auto max-w-5xl" />

      {/* METRICS */}
      <section id="metrics" className="relative px-6 md:px-10 py-32 overflow-hidden">
        {/* bg accent mesh */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[700px] rounded-full bg-accent/[0.02] blur-[100px]" />

        <div className="relative mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 40, filter: "blur(8px)" }}
            whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            viewport={{ margin: "-80px" }}
            transition={{ duration: 0.9, ease }}
            className="text-center mb-20"
          >
            <span className="text-[11px] font-bold uppercase tracking-[0.3em] text-accent/80">
              Metrics
            </span>
            <h2 className="mt-4 text-4xl font-bold tracking-tight md:text-5xl">
              Obsessively{" "}
              <span className="bg-gradient-to-r from-accent to-[#80ffb0] animate-gradient-text">
                precise.
              </span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {[
              { val: 171, suf: "", label: "Backend Tests", sub: "All green" },
              { val: 5, suf: "", label: "AI Engines", sub: "In parallel" },
              { val: 15, suf: "+", label: "Dimensions", sub: "Per repo scored" },
              { val: 12, suf: "", label: "App Routes", sub: "Full-stack" },
            ].map((s, i) => (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, y: 40, scale: 0.95, filter: "blur(6px)" }}
                whileInView={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
                viewport={{ margin: "-60px" }}
                transition={{ duration: 0.8, delay: i * 0.06, ease }}
              >
                <SpotlightCard className="p-7 md:p-8 text-center h-full">
                  <div className="font-mono text-4xl font-bold text-accent md:text-5xl">
                    <Counter to={s.val} suffix={s.suf} />
                  </div>
                  <div className="mt-2 text-sm font-medium text-primary">{s.label}</div>
                  <div className="mt-1 text-[12px] text-muted">{s.sub}</div>
                </SpotlightCard>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <div className="glow-line mx-auto max-w-5xl" />

      {/* DASHBOARD PREVIEW */}
      <section className="relative px-6 md:px-10 py-32 overflow-hidden">
        <motion.div
          initial={{ opacity: 0, y: 40, filter: "blur(8px)" }}
          whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          viewport={{ margin: "-80px" }}
          transition={{ duration: 0.9, ease }}
          className="mx-auto max-w-7xl text-center"
        >
          <span className="text-[11px] font-bold uppercase tracking-[0.3em] text-accent/80">
            Showcase
          </span>
          <h2 className="mt-4 mb-5 text-4xl font-bold tracking-tight md:text-5xl">
            Designed for{" "}
            <span className="bg-gradient-to-r from-accent to-[#80ffb0] animate-gradient-text">
              engineers.
            </span>
          </h2>
          <p className="mx-auto mb-16 max-w-md text-secondary/70">
            Every surface, every data point — built to help you ship the
            portfolio that gets noticed.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 80, rotateX: 6 }}
          whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
          viewport={{ margin: "-40px" }}
          transition={{ duration: 1.4, ease }}
          className="relative mx-auto max-w-5xl"
          style={{ perspective: 1200 }}
        >
          {/* Outer neon glow — intense */}
          <div className="pointer-events-none absolute -inset-16 rounded-3xl bg-accent/[0.04] blur-[100px] animate-pulse-glow" />
          <div className="pointer-events-none absolute -inset-8 rounded-3xl bg-gradient-to-b from-accent/[0.06] via-transparent to-accent/[0.03] blur-[60px]" />
          <div className="pointer-events-none absolute inset-x-0 -bottom-12 mx-auto h-40 w-3/4 rounded-full bg-accent/[0.06] blur-[80px]" />
          {/* Edge glow ring */}
          <div className="pointer-events-none absolute -inset-px rounded-2xl bg-gradient-to-b from-accent/20 via-accent/[0.03] to-accent/10" />

          <div className="overflow-hidden rounded-2xl border border-white/[0.06] bg-surface/80 backdrop-blur-xl shadow-[0_25px_80px_-20px_rgba(0,0,0,0.6)]">
            {/* Title bar */}
            <div className="flex items-center gap-2 border-b border-white/[0.04] px-5 py-3.5">
              <div className="h-3 w-3 rounded-full bg-[#ff5f57]" />
              <div className="h-3 w-3 rounded-full bg-[#febc2e]" />
              <div className="h-3 w-3 rounded-full bg-[#28c840]" />
              <span className="ml-4 font-mono text-[11px] text-muted">
                shortlist — dashboard
              </span>
            </div>

            <div className="min-h-[280px] sm:min-h-[360px]">
              {/* Mobile: no sidebar, just main. Desktop: sidebar + main */}
              <div className="hidden sm:grid grid-cols-12 h-full">
                {/* Sidebar */}
                <div className="col-span-3 border-r border-white/[0.04] bg-surface/60 p-4 md:p-5 space-y-1.5">
                  <div className="mb-4 md:mb-5 flex items-center gap-2">
                    <div className="h-2 w-2 rounded-[3px] bg-accent" />
                    <span className="text-[8px] md:text-[10px] font-bold tracking-[0.15em] uppercase text-muted">
                      Shortlist
                    </span>
                  </div>
                  {["Overview", "Analyze", "Projects", "Repo", "Scaffold", "Portfolio"].map(
                    (item, i) => (
                      <div
                        key={item}
                        className={`rounded-lg px-2 md:px-3 py-1.5 md:py-2 text-[9px] md:text-[11px] ${
                          i === 0
                            ? "bg-accent/[0.08] text-accent font-medium border border-accent/10"
                            : "text-muted/60"
                        }`}
                      >
                        {item}
                      </div>
                    )
                  )}
                </div>

                {/* Main */}
                <div className="col-span-9 bg-root/60 p-4 md:p-6 space-y-4 md:space-y-5">
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-[11px] md:text-[13px] font-semibold text-primary truncate">Good afternoon, Jayant</p>
                      <p className="text-[8px] md:text-[10px] text-muted mt-0.5">3 analyses this week</p>
                    </div>
                    <div className="shrink-0 rounded-lg bg-accent/[0.08] border border-accent/10 px-2 md:px-3 py-1 md:py-1.5 text-[8px] md:text-[10px] font-semibold text-accent whitespace-nowrap">+ New Analysis</div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 md:gap-3">
                    {[
                      { label: "Analyses", value: "24", pct: 75, color: "from-accent to-accent/60" },
                      { label: "Repos Scored", value: "12", pct: 55, color: "from-info to-info/60" },
                      { label: "Scaffolds", value: "8", pct: 90, color: "from-[#c084fc] to-[#c084fc]/60" },
                    ].map((card) => (
                      <div
                        key={card.label}
                        className="rounded-xl border border-white/[0.04] bg-surface/40 p-2.5 md:p-4 space-y-1.5 md:space-y-2.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[8px] md:text-[10px] text-muted font-medium">{card.label}</span>
                          <span className="h-1.5 w-1.5 md:h-2 md:w-2 rounded-sm bg-accent/20" />
                        </div>
                        <p className="text-[14px] md:text-[18px] font-bold text-primary">{card.value}</p>
                        <div className="h-1 md:h-1.5 w-full rounded-full bg-edge/30 overflow-hidden">
                          <div
                            className={`h-full rounded-full bg-gradient-to-r ${card.color}`}
                            style={{ width: `${card.pct}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                  {/* Recent row */}
                  <div className="space-y-1.5 mt-1">
                    <p className="text-[8px] md:text-[10px] font-semibold text-muted/70 uppercase tracking-wider">Recent</p>
                    {["Senior Frontend Engineer \u2014 Stripe", "ML Engineer \u2014 Meta"].map((r) => (
                      <div key={r} className="flex items-center gap-2 rounded-lg bg-surface/30 border border-white/[0.03] px-2 md:px-3 py-1.5 md:py-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-accent/60" />
                        <span className="text-[8px] md:text-[10px] text-secondary/80 truncate">{r}</span>
                        <span className="ml-auto text-[7px] md:text-[8px] text-muted shrink-0">\u2713 completed</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Mobile-only simplified view */}
              <div className="sm:hidden p-4 bg-root/60 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[12px] font-semibold text-primary">Good afternoon, Jayant</p>
                    <p className="text-[9px] text-muted mt-0.5">3 analyses this week</p>
                  </div>
                  <div className="rounded-lg bg-accent/[0.08] border border-accent/10 px-2.5 py-1.5 text-[9px] font-semibold text-accent">+ New</div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { label: "Analyses", value: "24", pct: 75, color: "from-accent to-accent/60" },
                    { label: "Repos", value: "12", pct: 55, color: "from-info to-info/60" },
                    { label: "Scaffolds", value: "8", pct: 90, color: "from-[#c084fc] to-[#c084fc]/60" },
                  ].map((card) => (
                    <div
                      key={card.label}
                      className="rounded-xl border border-white/[0.04] bg-surface/40 p-2.5 space-y-1.5"
                    >
                      <span className="text-[8px] text-muted font-medium block">{card.label}</span>
                      <p className="text-[16px] font-bold text-primary">{card.value}</p>
                      <div className="h-1 w-full rounded-full bg-edge/30 overflow-hidden">
                        <div
                          className={`h-full rounded-full bg-gradient-to-r ${card.color}`}
                          style={{ width: `${card.pct}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="space-y-1.5">
                  <p className="text-[9px] font-semibold text-muted/70 uppercase tracking-wider">Recent</p>
                  {["Senior Frontend \u2014 Stripe", "ML Engineer \u2014 Meta"].map((r) => (
                    <div key={r} className="flex items-center gap-2 rounded-lg bg-surface/30 border border-white/[0.03] px-2.5 py-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-accent/60 shrink-0" />
                      <span className="text-[9px] text-secondary/80 truncate">{r}</span>
                      <span className="ml-auto text-[8px] text-muted shrink-0">\u2713</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* CTA */}
      <section className="relative px-6 md:px-10 py-32">
        <motion.div
          initial={{ opacity: 0, y: 60, scale: 0.96 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ margin: "-40px" }}
          transition={{ duration: 1.2, ease }}
          className="relative mx-auto max-w-5xl overflow-hidden rounded-3xl"
        >
          {/* bg mesh */}
          <div className="absolute inset-0">
            <div className="absolute inset-0 bg-surface/90" />
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[400px] w-[500px] rounded-full bg-accent/[0.06] blur-[100px]" />
            <div className="absolute left-1/4 top-0 h-[300px] w-[300px] rounded-full bg-[#c084fc]/[0.03] blur-[80px]" />
            <div className="absolute right-1/4 bottom-0 h-[300px] w-[300px] rounded-full bg-info/[0.03] blur-[80px]" />
            <div className="absolute inset-0 grid-pattern opacity-30" />
          </div>

          {/* border glow */}
          <div className="absolute -inset-px rounded-3xl bg-gradient-to-b from-accent/15 via-transparent to-accent/5" />

          <div className="relative z-10 p-10 py-24 md:p-20 md:py-32 text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ margin: "-40px" }}
              transition={{ duration: 0.7, delay: 0.15, ease }}
              className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/[0.05] px-4 py-2"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-40" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
              </span>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-accent/80">
                Free forever
              </span>
            </motion.div>

            <h2 className="text-4xl font-bold tracking-tight md:text-5xl lg:text-6xl">
              Your next role
              <br />
              is{" "}
              <span className="bg-gradient-to-r from-accent via-[#e8ff66] to-accent animate-gradient-text">
                waiting.
              </span>
            </h2>
            <p className="mx-auto mt-6 mb-10 max-w-lg text-secondary/70 leading-relaxed">
              Stop guessing what recruiters want. Let AI architect a portfolio
              that proves you&apos;re the engineer they&apos;re looking for.
            </p>
            {user ? (
              <Link
                href="/dashboard"
                className="group inline-flex items-center gap-2.5 rounded-full bg-accent px-10 py-4 text-sm font-bold text-root transition-all hover:shadow-[0_0_50px_rgba(200,255,0,0.35)]"
              >
                Go to Dashboard
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            ) : (
              <button
                onClick={() => setShowAuth(true)}
                className="group relative overflow-hidden inline-flex items-center gap-2.5 rounded-full bg-accent px-10 py-4 text-sm font-bold text-root transition-all hover:shadow-[0_0_50px_rgba(200,255,0,0.35)]"
              >
                <span className="absolute inset-0 beam" />
                <span className="relative">Get started — it&apos;s free</span>
                <ArrowRight className="relative h-4 w-4 transition-transform group-hover:translate-x-1" />
              </button>
            )}
          </div>
        </motion.div>
      </section>

      <footer className="relative border-t border-white/[0.04] overflow-hidden">
        {/* Aurora shader background */}
        <div className="absolute inset-0 opacity-30">
          <DarkVeil hueShift={120} speed={0.2} noiseIntensity={0.3} scanlineIntensity={0.0} warpAmount={0.5} resolutionScale={0.4} />
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-root via-root/95 to-root/80" />

        <div className="relative z-10 py-14">
          <div className="mx-auto flex max-w-7xl flex-col items-center gap-8 px-6 md:flex-row md:justify-between md:px-10">
            <div className="flex items-center gap-2.5">
              <div className="relative h-3 w-3">
                <div className="absolute inset-0 rounded-[3px] bg-accent" />
                <div className="absolute inset-0 rounded-[3px] bg-accent blur-[6px] opacity-50" />
              </div>
              <span className="text-[12px] font-bold tracking-[0.2em] uppercase text-primary/90">
                Shortlist
              </span>
            </div>
            <div className="flex gap-8">
              {["Features", "Process", "Metrics"].map((l) => (
                <a
                  key={l}
                  href={`#${l.toLowerCase()}`}
                  className="text-[12px] text-secondary/80 hover:text-accent transition-colors duration-300 font-medium"
                >
                  {l}
                </a>
              ))}
            </div>
            <p className="text-[11px] text-muted/60">
              &copy; {new Date().getFullYear()} Shortlist By Eklavya
            </p>
          </div>
        </div>
      </footer>
    </SmoothScrollProvider>
  );
}
