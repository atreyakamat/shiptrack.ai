import Link from "next/link";
import { BarChart3, Bell, Boxes, ScanLine, Sparkles, Timer, ArrowRight, Check } from "lucide-react";
import { Logo } from "@/components/Logo";

const FEATURES = [
  { icon: Boxes, title: "One dashboard", body: "Every shipment, every carrier, in one clean view with live status and search." },
  { icon: Timer, title: "Visual timeline", body: "See the full routing history of any parcel, scan by scan." },
  { icon: ScanLine, title: "Receipt scanner", body: "Upload a postal receipt and we pull the tracking number out for you." },
  { icon: Sparkles, title: "AI insights", body: "Plain-language summaries, delay analysis and what to do next." },
  { icon: BarChart3, title: "Analytics", body: "Delivery rate, transit times and where your parcels spend their time." },
  { icon: Bell, title: "Notifications", body: "Get told when something is out for delivery, delivered, or stuck." },
];

const STEPS = [
  ["Add", "Paste a tracking number or scan a receipt."],
  ["Track", "We refresh status and normalise every carrier's scans."],
  ["Understand", "AI explains the journey and flags what needs attention."],
];

export default function Landing() {
  return (
    <div className="relative overflow-hidden">
      <div aria-hidden className="pointer-events-none absolute inset-x-0 top-0 -z-0 h-[720px] bg-[radial-gradient(ellipse_at_top,rgba(56,189,248,0.18),transparent_60%),radial-gradient(ellipse_at_80%_10%,rgba(129,140,248,0.15),transparent_50%)]" />

      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Logo />
        <nav className="flex items-center gap-2">
          <a href="#features" className="btn hidden text-muted hover:text-white sm:inline-flex">Features</a>
          <a href="#how" className="btn hidden text-muted hover:text-white sm:inline-flex">How it works</a>
          <Link href="/login" className="btn-ghost">Sign in</Link>
        </nav>
      </header>

      <main className="relative z-10">
        <section className="mx-auto max-w-4xl px-6 pb-24 pt-20 text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-sky/20 bg-panel/60 px-4 py-1.5 text-sm font-medium text-sky">
            <span className="h-2 w-2 rounded-full bg-sky" /> Shipment intelligence for everyone
          </span>
          <h1 className="mt-8 font-display text-5xl font-bold leading-[1.05] sm:text-6xl md:text-7xl">
            Track smarter.<br /><span className="gradient-text">Understand deliveries.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted">
            ShipTrack AI turns scattered postal scans into a clear story — where your parcel is,
            whether it&apos;s healthy, and what happens next. Built for individuals, creators and small businesses.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href="/login?mode=register" className="btn-primary px-6 py-3 text-base">
              Get started free <ArrowRight size={18} aria-hidden />
            </Link>
            <Link href="/login?demo=1" className="btn-ghost px-6 py-3 text-base">Try the demo</Link>
          </div>
        </section>

        <section className="mx-auto max-w-5xl px-6 pb-24" aria-label="Product preview">
          <div className="card p-4 shadow-2xl shadow-sky/5 sm:p-6">
            <div className="grid gap-3 sm:grid-cols-4">
              {[["Total", "9"], ["In transit", "1"], ["Delivered", "2"], ["Needs attention", "1"]].map(([k, v]) => (
                <div key={k} className="rounded-xl border border-line bg-ink p-4">
                  <p className="text-xs uppercase tracking-wide text-muted">{k}</p>
                  <p className="mt-1 font-display text-3xl font-bold">{v}</p>
                </div>
              ))}
            </div>
            <ul className="mt-3 divide-y divide-line rounded-xl border border-line bg-ink text-sm">
              {[["EM100000002IN", "Pune Sorting Hub", "In transit", "text-sky"], ["EM100000004IN", "Bambavada S.O", "Delivered", "text-emerald-400"], ["EM100000005IN", "Kolkata", "Exception", "text-amber-400"]].map(([n, l, s, c]) => (
                <li key={n} className="flex items-center justify-between px-4 py-3">
                  <span className="font-mono">{n}</span>
                  <span className="hidden text-muted sm:inline">{l}</span>
                  <span className={`font-medium ${c}`}>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section id="features" className="mx-auto max-w-6xl scroll-mt-8 px-6 pb-24">
          <h2 className="text-center font-display text-3xl font-bold sm:text-4xl">Everything about your deliveries</h2>
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, body }) => (
              <div key={title} className="card p-6 transition hover:border-sky/40">
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-sky/10 text-sky"><Icon size={20} aria-hidden /></span>
                <h3 className="mt-4 font-display text-lg font-semibold">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="how" className="mx-auto max-w-4xl scroll-mt-8 px-6 pb-24">
          <h2 className="text-center font-display text-3xl font-bold sm:text-4xl">How it works</h2>
          <ol className="mt-12 grid gap-5 sm:grid-cols-3">
            {STEPS.map(([t, b], i) => (
              <li key={t} className="card p-6">
                <span className="font-display text-sm font-bold text-sky">0{i + 1}</span>
                <h3 className="mt-2 font-display text-xl font-semibold">{t}</h3>
                <p className="mt-2 text-sm text-muted">{b}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="mx-auto max-w-3xl px-6 pb-24 text-center">
          <div className="card p-10">
            <h2 className="font-display text-3xl font-bold">Ready to know where everything is?</h2>
            <ul className="mx-auto mt-5 inline-flex flex-col gap-2 text-left text-sm text-muted">
              {["Free to start", "Demo data included", "No card required"].map((t) => (
                <li key={t} className="flex items-center gap-2"><Check size={16} className="text-sky" aria-hidden />{t}</li>
              ))}
            </ul>
            <div className="mt-8"><Link href="/login?mode=register" className="btn-primary px-6 py-3 text-base">Create your account</Link></div>
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-t border-line px-6 py-8 text-center text-sm text-muted">
        <p>© {new Date().getFullYear()} ShipTrack AI · Designed &amp; developed by <span className="gradient-text font-semibold">Atreya Kamat</span></p>
      </footer>
    </div>
  );
}
