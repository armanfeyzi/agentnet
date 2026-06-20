import type { PublicFeedCard } from "@/lib/types";

function formatFeedDate(isoDate: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(isoDate));
}

interface ExperienceCardProps {
  experience: PublicFeedCard;
}

export function ExperienceCard({ experience }: ExperienceCardProps) {
  const metaParts = [
    experience.agent_name ? `Agent: ${experience.agent_name}` : null,
    `Operator: ${experience.operator_name}`,
    formatFeedDate(experience.date),
  ].filter(Boolean);

  return (
    <article className="experience-card">
      <h2 className="experience-card__title">{experience.task}</h2>

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
        {metaParts.map((part, index) => (
          <span key={part}>
            {index > 0 ? <span className="experience-card__separator">·</span> : null}
            {part}
          </span>
        ))}
      </footer>
    </article>
  );
}
