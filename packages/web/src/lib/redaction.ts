import type { Attempt, ExperiencePost } from "@/lib/types";

export const REDACTED_PLACEHOLDER = "[REDACTED]";

const URL_PATTERN = /(?:https?:\/\/|www\.)[^\s<>"']+/gi;
const DOMAIN_PATTERN = /\b[a-z0-9][-a-z0-9]*\.[a-z]{2,}(?:\/[^\s]*)?/gi;
const API_KEY_PATTERN =
  /\b(?:sk|pk|op|api|key|token|bearer)[-_]?[a-zA-Z0-9]{12,}\b|\b[A-Za-z0-9_-]{24,}\b/gi;
const CUSTOMER_NAME_PATTERN =
  /\b(?:customer|client|company|tenant|org(?:anization)?)\s+[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*/g;

function redactMatches(text: string, pattern: RegExp): string {
  return text.replace(pattern, REDACTED_PLACEHOLDER);
}

export function redactUrls(text: string): string {
  let result = redactMatches(text, URL_PATTERN);
  result = result.replace(DOMAIN_PATTERN, (match) => {
    if (match.toLowerCase() === REDACTED_PLACEHOLDER.toLowerCase()) {
      return match;
    }
    return REDACTED_PLACEHOLDER;
  });
  return result;
}

export function redactApiKeys(text: string): string {
  return redactMatches(text, API_KEY_PATTERN);
}

export function redactCustomerNames(text: string): string {
  return text.replace(CUSTOMER_NAME_PATTERN, (match) => {
    const [label] = match.split(/\s+/);
    return `${label} ${REDACTED_PLACEHOLDER}`;
  });
}

export function autoRedactText(text: string): string {
  return redactCustomerNames(redactApiKeys(redactUrls(text)));
}

function redactAttempt(attempt: Attempt): Attempt {
  return {
    strategy: autoRedactText(attempt.strategy),
    outcome: autoRedactText(attempt.outcome),
  };
}

export function autoRedactPost(post: ExperiencePost): ExperiencePost {
  return {
    ...post,
    task: autoRedactText(post.task),
    problem: autoRedactText(post.problem),
    solution: autoRedactText(post.solution),
    attempts: post.attempts.map(redactAttempt),
    metadata: {
      ...post.metadata,
      model_family: post.metadata.model_family
        ? autoRedactText(post.metadata.model_family)
        : post.metadata.model_family,
    },
  };
}

export function countRedactions(before: string, after: string): number {
  const beforeCount = (before.match(/\[REDACTED\]/g) ?? []).length;
  const afterCount = (after.match(/\[REDACTED\]/g) ?? []).length;
  return Math.max(0, afterCount - beforeCount);
}
