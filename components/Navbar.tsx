"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Logo from "./Logo";
import { cx } from "@/lib/utils";

const LINKS = [
  { href: "/citizen-request", label: "Submit Request" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/hotspot-map", label: "Hotspot Map" },
  { href: "/insights", label: "Insights" },
  { href: "/methodology", label: "Methodology" },
];

export default function Navbar() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-base/95 backdrop-blur">
      <nav
        className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6"
        aria-label="Primary"
      >
        <Link href="/" className="focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light rounded-sm">
          <Logo />
        </Link>
        <ul className="hidden items-center gap-1 md:flex">
          {LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className={cx(
                    "rounded-sm px-3 py-2 text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light",
                    active ? "text-text" : "text-muted hover:text-text"
                  )}
                >
                  {link.label}
                </Link>
              </li>
            );
          })}
        </ul>
        <Link
          href="/citizen-request"
          className="rounded-sm bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-light md:inline-block hidden"
        >
          Submit a Request
        </Link>
      </nav>
    </header>
  );
}
