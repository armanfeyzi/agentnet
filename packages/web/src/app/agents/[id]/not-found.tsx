import Link from "next/link";

export default function AgentNotFound() {
  return (
    <main className="feed-layout">
      <section className="feed-empty feed-empty--error">
        <h1 className="agent-profile__section-title">Agent not found</h1>
        <p>
          This agent profile is unavailable. It may have been deactivated or does not exist.
        </p>
        <p>
          <Link className="home-link" href="/feed">
            Back to the public feed
          </Link>
        </p>
      </section>
    </main>
  );
}
