import { notFound } from "next/navigation";
import SendButton from "./SendButton";

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
      <div
        style={{
          background: "#111",
          padding: "12px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <span
          style={{
            color: "#fff",
            fontFamily: "Georgia, serif",
            fontSize: "16px",
            fontWeight: 700,
            letterSpacing: "-0.3px",
          }}
        >
          The Operating Brief — Preview
        </span>
        <SendButton token={token} />
      </div>
      <iframe
        src={`/api/preview/${token}/html`}
        style={{
          width: "100%",
          height: "calc(100vh - 48px)",
          border: "none",
          display: "block",
        }}
      />
    </div>
  );
}
