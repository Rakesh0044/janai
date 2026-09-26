export default function DemoModeBanner({ visible }: { visible: boolean }) {
  if (!visible) return null;
  return (
    <div
      role="status"
      className="flex items-center gap-2 border border-accent/40 bg-accent/10 px-4 py-2.5 text-sm text-accent"
    >
      <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
      Showing synthetic demo data — the backend is unreachable or demo mode is forced.
    </div>
  );
}
