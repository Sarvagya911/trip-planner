"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { MapPin } from "lucide-react";

export function Nav() {
  const pathname = usePathname();
  const isHome = pathname === "/";
  const [scrolled, setScrolled] = useState(!isHome);

  useEffect(() => {
    if (!isHome) {
      setScrolled(true);
      return;
    }
    const onScroll = () => setScrolled(window.scrollY > 60);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [isHome]);

  const links = [
    { href: "/", label: "Home" },
    { href: "/features", label: "Features" },
    { href: "/plan", label: "Plan a Trip" },
  ];

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 transition-all duration-500"
      style={
        scrolled
          ? {
              background: "rgba(45,31,74,0.55)",
              backdropFilter: "blur(16px)",
              borderBottom: "0.5px solid rgba(255,255,255,0.14)",
            }
          : { background: "transparent", borderBottom: "0.5px solid transparent" }
      }
    >
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight text-white">
          <MapPin size={18} style={{ color: "#F0B87A" }} />
          Trip Planner
        </Link>

        <div className="flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm font-medium px-3.5 py-2 rounded-lg transition-colors"
              style={
                pathname === l.href
                  ? { background: "rgba(240,184,122,0.18)", color: "#F0B87A" }
                  : { color: "rgba(255,255,255,0.75)" }
              }
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}