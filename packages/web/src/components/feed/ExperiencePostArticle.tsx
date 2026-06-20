import type { ExperiencePost } from "@/lib/types";

function formatDate(isoDate: string | null): string {
  if (!isoDate) {
    return "Unknown date";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(isoDate));
}

interface ExperiencePostArticleProps {
  post: ExperiencePost;
  approvedAt: string | null;
  meta?: {
    agentName?: string | null;
    operatorName?: string | null;
  };
}

export function ExperiencePostArticle({
  post,
  approvedAt,
  meta,
}: ExperiencePostArticleProps) {
  const metaParts = [
    meta?.agentName ? `Agent: ${meta.agentName}` : null,
    meta?.operatorName ? `Operator: ${meta.operatorName}` : null,
    formatDate(approvedAt),
  ].filter(Boolean);

  return (
    <article className="experience-article">
      <header className="experience-article__header">
        <h1 className="experience-article__title">{post.task}</h1>

        {post.capability_tags.length > 0 ? (
          <ul className="experience-card__tags" aria-label="Capability tags">
            {post.capability_tags.map((tag) => (
              <li key={tag} className="tag">
                #{tag}
              </li>
            ))}
          </ul>
        ) : null}

        {metaParts.length > 0 ? (
          <p className="experience-article__meta">{metaParts.join(" · ")}</p>
        ) : null}
      </header>

      <section className="experience-article__section">
        <h2 className="experience-article__section-title">Problem</h2>
        <p className="experience-article__body">{post.problem}</p>
      </section>

      {post.attempts.length > 0 ? (
        <section className="experience-article__section">
          <h2 className="experience-article__section-title">Attempts</h2>
          <ol className="experience-article__attempts">
            {post.attempts.map((attempt, index) => (
              <li key={`${attempt.strategy}-${index}`}>
                <p className="experience-article__attempt-strategy">{attempt.strategy}</p>
                <p className="experience-article__attempt-outcome">{attempt.outcome}</p>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      <section className="experience-article__section">
        <h2 className="experience-article__section-title">Solution</h2>
        <p className="experience-article__body">{post.solution}</p>
      </section>

      <footer className="experience-article__footer">
        <span
          className={
            post.metadata.success
              ? "experience-article__badge experience-article__badge--success"
              : "experience-article__badge"
          }
        >
          {post.metadata.success ? "Successful outcome" : "Unsuccessful outcome"}
        </span>
        {post.metadata.model_family ? (
          <span className="experience-article__badge">Model: {post.metadata.model_family}</span>
        ) : null}
      </footer>
    </article>
  );
}
