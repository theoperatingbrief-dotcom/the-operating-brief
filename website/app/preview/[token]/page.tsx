import { notFound } from "next/navigation";
import AdminControls from "./AdminControls";

export default async function PreviewPage({
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
      <AdminControls token={token} />
    </div>
  );
}
