import { notFound } from "next/navigation";

export default async function MarketsPreviewPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  if (token !== process.env.PREVIEW_TOKEN) {
    notFound();
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f5f4f0" }}>
      <iframe
        src={`/api/markets/preview/${token}/html`}
        style={{ width: "100%", height: "100vh", border: "none", display: "block" }}
        title="The Markets Brief Preview"
      />
    </div>
  );
}
