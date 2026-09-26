// Placeholder wordmark used until the real JanDrishti AI logo file is supplied.
// Drop the actual logo at /public/logo.svg (or .png) and replace the JSX
// below with an <img src="/logo.svg" /> — keep this component as the single
// place the mark is rendered so branding stays consistent across the app.

export default function Logo({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dims = { sm: 22, md: 28, lg: 36 }[size];
  const text = { sm: "text-sm", md: "text-base", lg: "text-xl" }[size];
  return (
    <div className="flex items-center gap-2.5">
      <svg width={dims} height={dims} viewBox="0 0 40 40" fill="none" aria-hidden="true">
        <rect x="1" y="1" width="38" height="38" rx="4" stroke="#4A9291" strokeWidth="1.5" />
        <path d="M12 27V13l8 9 8-9v14" stroke="#C98A2C" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className={`font-display ${text} tracking-tight text-text`}>
        JanDrishti <span className="text-primary-light">AI</span>
      </span>
    </div>
  );
}
