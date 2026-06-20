import { DraftPostEditor } from "@/components/DraftPostEditor";

export default async function DraftEditPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <DraftPostEditor draftId={id} />;
}
