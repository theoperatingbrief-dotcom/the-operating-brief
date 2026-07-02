export function getAdminSecret() {
  return process.env.ADMIN_PASSWORD || process.env.PREVIEW_TOKEN || "";
}
