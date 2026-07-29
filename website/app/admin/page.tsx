import AdminDashboard from "./AdminDashboard";

export default function AdminPage() {
  return (
    <AdminDashboard
      previewToken={process.env.PREVIEW_TOKEN ?? ""}
      isVercel={!!process.env.VERCEL}
    />
  );
}
