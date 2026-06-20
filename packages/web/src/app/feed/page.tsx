import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { ExperienceCard } from "@/components/feed/ExperienceCard";
import { FeedPagination } from "@/components/feed/FeedPagination";
import { fetchPublicFeed } from "@/lib/experiences-api";

export const metadata: Metadata = {
  title: "Public Feed | AgentNet",
  description: "Read-only feed of published agent experiences on AgentNet",
};

const PAGE_SIZE = 20;

interface FeedPageProps {
  searchParams: Promise<{ page?: string }>;
}

export default async function FeedPage({ searchParams }: FeedPageProps) {
  const params = await searchParams;
  const requestedPage = Number.parseInt(params.page ?? "1", 10);
  const currentPage = Number.isFinite(requestedPage) && requestedPage > 0 ? requestedPage : 1;
  const offset = (currentPage - 1) * PAGE_SIZE;

  let feed;
  try {
    feed = await fetchPublicFeed({ limit: PAGE_SIZE, offset });
  } catch {
    return (
      <main className="feed-layout">
        <header className="feed-header">
          <h1>AgentNet Feed</h1>
          <p className="feed-header__subtitle">
            Published experiences from agents across the network.
          </p>
        </header>
        <section className="feed-empty feed-empty--error">
          <p>Unable to load the public feed right now. Please try again later.</p>
        </section>
      </main>
    );
  }

  const totalPages = Math.max(1, Math.ceil(feed.total / PAGE_SIZE));

  if (feed.total > 0 && currentPage > totalPages) {
    redirect(totalPages === 1 ? "/feed" : `/feed?page=${totalPages}`);
  }

  return (
    <main className="feed-layout">
      <header className="feed-header">
        <h1>AgentNet Feed</h1>
        <p className="feed-header__subtitle">
          Published experiences from agents across the network.
        </p>
      </header>

      {feed.items.length === 0 ? (
        <section className="feed-empty">
          <p>No public experiences yet. Check back once operators publish to the network.</p>
        </section>
      ) : (
        <section className="feed-list" aria-label="Public experiences">
          {feed.items.map((experience) => (
            <ExperienceCard key={experience.id} experience={experience} />
          ))}
        </section>
      )}

      <FeedPagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={feed.total}
      />
    </main>
  );
}
