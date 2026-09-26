import Logo from "./Logo";

export default function Footer() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto max-w-7xl px-6 py-10 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <Logo size="sm" />
        <p className="text-sm text-muted max-w-xl">
          Prototype insight platform built on synthetic/demo data for demonstration
          purposes. Not affiliated with any government body and not a source of
          official infrastructure or funding decisions.
        </p>
      </div>
    </footer>
  );
}
