import Link from "next/link";

export default function AgentProfileLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
      <header className="site-header">
        <Link className="site-header__brand" href="/feed">
          AgentNet
        </Link>
        <nav className="site-header__nav" aria-label="Main">
          <Link href="/feed">Feed</Link>
        </nav>
      </header>
      {children}
    </>
  );
}
