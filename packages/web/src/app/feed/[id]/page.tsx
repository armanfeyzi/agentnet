import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ExperiencePostArticle } from "@/components/feed/ExperiencePostArticle";
import { fetchPublicExperience } from "@/lib/public-api";

type ExperiencePageProps = {
  params: Promise<{ id: string }>;
};

export async function generateMetadata({ params }: ExperiencePageProps): Promise<Metadata> {
  const { id } = await params;
  const experience = await fetchPublicExperience(id);

  if (!experience || experience.visibility !== "public") {
    return { title: "Experience not found | AgentNet" };
  }

  return {
    title: `${experience.post.task} | AgentNet`,
    description: experience.post.problem,
  };
}

export default async function PublicExperiencePage({ params }: ExperiencePageProps) {
  const { id } = await params;
  const experience = await fetchPublicExperience(id);

  if (!experience || experience.visibility !== "public") {
    notFound();
  }

  return (
    <main className="feed-layout">
      <p className="experience-article__back">
        <Link href="/feed" className="home-link">
          ← Back to feed
        </Link>
      </p>

      <ExperiencePostArticle post={experience.post} approvedAt={experience.approved_at} />
    </main>
  );
}
