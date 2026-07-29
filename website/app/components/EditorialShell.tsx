import Link from "next/link";
import type { ReactNode } from "react";

const NAV_LINKS = [
  { label: "The Operating Brief", href: "/" },
  { label: "The Sporting Brief", href: "/sporting" },
  { label: "The Markets Brief", href: "/markets" },
];

type EditorialShellProps = {
  activeHref: string;
  eyebrow: string;
  title: string;
  subtitle: string;
  archiveHref?: string;
  archiveLabel?: string;
  footerCopy: string;
  children: ReactNode;
};

export function EditorialShell({
  activeHref,
  eyebrow,
  title,
  subtitle,
  archiveHref,
  archiveLabel = "View archive",
  footerCopy,
  children,
}: EditorialShellProps) {
  return (
    <div className="page-frame">
      <div className="page-shell">
        <nav className="brief-nav" aria-label="Brief navigation">
          {NAV_LINKS.map((link) => {
            const active = link.href === activeHref;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`brief-nav__link ${active ? "is-active" : ""}`}
                aria-current={active ? "page" : undefined}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <header className="hero">
          <div className="hero__meta">
            <p className="eyebrow">{eyebrow}</p>
            {archiveHref ? (
              <Link href={archiveHref} className="archive-link">
                {archiveLabel}
              </Link>
            ) : null}
          </div>

          <h1 className="hero__title">{title}</h1>
          <p className="hero__subtitle">{subtitle}</p>
        </header>

        <div className="content-stack">{children}</div>

        <footer className="page-footer">
          <p className="page-footer__copy">{footerCopy}</p>
          <p className="page-footer__links">
            <Link href="/privacy">Privacy Policy</Link>
            <Link href="/terms">Terms of Use</Link>
          </p>
        </footer>
      </div>
    </div>
  );
}
