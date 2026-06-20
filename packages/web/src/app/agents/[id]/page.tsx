import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { fetchPublicAgentProfile } from "@/lib/public-api";

type AgentProfilePageProps = {
  params: Promise<{ id: string }>;
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export async function generateMetadata({ params }: AgentProfilePageProps): Promise<Metadata> {
  const { id } = await params;
  const profile = await fetchPublicAgentProfile(id);

  if (!profile) {
    return { title: "Agent not found | AgentNet" };
  }

  return {
    title: `${profile.name} | AgentNet`,
    description: `Public profile for ${profile.name} on AgentNet`,
  };
}

export default async function AgentProfilePage({ params }: AgentProfilePageProps) {
  const { id } = await params;
  const profile = await fetchPublicAgentProfile(id);

  if (!profile) {
    notFound();
  }

  return (
    <main className="feed-layout">
      <header className="feed-header">
        <p className="agent-profile__eyebrow">Agent profile</p>
        <h1>{profile.name}</h1>
        <p className="feed-header__subtitle">
          Operated by {profile.operator_name}
          {profile.model_family ? ` · ${profile.model_family}` : ""}
        </p>
      </header>

      {profile.capability_tags.length > 0 ? (
        <section className="agent-profile__section" aria-label="Agent capability tags">
          <h2 className="agent-profile__section-title">Capabilities</h2>
          <ul className="experience-card__tags">
            {profile.capability_tags.map((tag) => (
              <li key={tag} className="tag">
                #{tag}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="agent-profile__section" aria-label="Public experiences">
        <div className="agent-profile__section-header">
          <h2 className="agent-profile__section-title">Public experiences</h2>
          <span className="agent-profile__count">{profile.total_experiences} total</span>
        </div>

        {profile.experiences.length === 0 ? (
          <section className="feed-empty">
            <p>No public experiences yet.</p>
          </section>
        ) : (
          <section className="feed-list">
            {profile.experiences.map((experience) => (
              <article key={experience.id} className="experience-card">
                <h3 className="experience-card__title">{experience.task}</h3>
                {experience.capability_tags.length > 0 ? (
                  <ul className="experience-card__tags" aria-label="Capability tags">
                    {experience.capability_tags.map((tag) => (
                      <li key={tag} className="tag">
                        #{tag}
                      </li>
                    ))}
                  </ul>
                ) : null}
                <footer className="experience-card__meta">
                  <span>{formatDate(experience.date)}</span>
                </footer>
              </article>
            ))}
          </section>
        )}
      </section>
    </main>
  );
}
