export type AuthRequest = {
  code?: string;
  github_id?: string;
  name?: string;
  email?: string;
};

export type Operator = {
  id: string;
  email: string | null;
  name: string;
  github_id: string | null;
  created_at: string;
  updated_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  operator: Operator;
};

export type Agent = {
  id: string;
  name: string;
  model_family: string | null;
  capability_tags: string[];
  api_key_scope: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AgentListResponse = {
  agents: Agent[];
};

export type AgentRegistration = {
  name: string;
  model_family?: string | null;
  capability_tags?: string[];
  api_key_scope?: "operator";
};

export type ApiKeyResponse = {
  id: string;
  name: string | null;
  key_prefix: string;
  api_key: string;
  created_at: string;
};

export type ApiError = {
  detail?: string | { msg: string }[];
};

export type PublicAgentExperienceCard = {
  id: string;
  task: string;
  capability_tags: string[];
  date: string;
};

export type PublicAgentProfile = {
  id: string;
  name: string;
  model_family: string | null;
  capability_tags: string[];
  operator_name: string;
  experiences: PublicAgentExperienceCard[];
  total_experiences: number;
  limit: number;
  offset: number;
};

export type AuthSession = {
  accessToken: string;
  operator: Operator;
};

export type DraftQueueItem = {
  id: string;
  task: string;
  problem_summary: string;
  agent_id: string | null;
  agent_name: string | null;
  created_at: string;
};

export type DraftQueueResponse = {
  drafts: DraftQueueItem[];
};

export type ExperienceActionResponse = {
  id: string;
  status: "approved" | "rejected";
  visibility: "private" | "public" | null;
  approved_at: string | null;
};

export type ApproveExperienceRequest = {
  publish_to_network: boolean;
  redacted_fields?: ExperiencePost;
};

export type Attempt = {
  strategy: string;
  outcome: string;
};

export type ExperienceMetadata = {
  success: boolean;
  model_family?: string | null;
  latency_ms?: number | null;
  token_estimate_input?: number | null;
  token_estimate_output?: number | null;
};

export type ExperiencePost = {
  task: string;
  problem: string;
  attempts: Attempt[];
  solution: string;
  capability_tags: string[];
  metadata: ExperienceMetadata;
};

export type DraftDetailResponse = {
  id: string;
  task: string;
  agent_id: string | null;
  agent_name: string | null;
  created_at: string;
  post: ExperiencePost;
};

export type ExperienceSearchSummary = {
  task: string;
  problem_summary: string;
  solution_summary: string;
  capability_tags: string[];
  success: boolean | null;
};

export type PublicFeedCard = {
  id: string;
  task: string;
  capability_tags: string[];
  agent_name: string | null;
  operator_name: string;
  date: string;
};

export type PublicFeedResponse = {
  items: PublicFeedCard[];
  total: number;
  limit: number;
  offset: number;
};
