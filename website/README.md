# Website

This is the Next.js App Router site for The Operating Brief newsletter suite. It handles public subscription pages, archives, unsubscribe flows, admin controls, and token-protected Operating Brief preview approval.

For overall product intent and backend generator context, read the root `README.md` first.

## Main Surfaces

- `/` - The Operating Brief subscribe page, including referral code capture.
- `/markets` - The Markets Brief subscribe page.
- `/sporting` - The Sporting Brief subscribe page.
- `/archive` and `/archive/[slug]` - Operating Brief archive.
- `/markets/archive` and `/markets/archive/[slug]` - Markets archive.
- `/sporting/archive` and `/sporting/archive/[slug]` - Sporting archive.
- `/unsubscribe`, `/markets/unsubscribe`, `/sporting/unsubscribe` - unsubscribe pages.
- `/admin` - password-protected dashboard for subscriber counts and generator jobs.
- `/preview/[token]` - token-protected Operating Brief draft controls.

## API Routes

- `/api/subscribe` - Operating Brief subscribe/reactivate, welcome email, referral link creation.
- `/api/markets/subscribe` - Markets Brief subscribe/reactivate and welcome email.
- `/api/sporting/subscribe` - Sporting Brief subscribe/reactivate and welcome email.
- `/api/unsubscribe` - Operating Brief unsubscribe.
- `/api/markets/unsubscribe` - Markets unsubscribe.
- `/api/sporting/unsubscribe` - Sporting unsubscribe.
- `/api/admin/login` - admin password check.
- `/api/admin/subscribers` - active subscriber counts for Operating, Markets, Sporting, and Paddock.
- `/api/admin/run` - streams Python generator output for preview/send jobs.
- `/api/preview/[token]/generate` - dispatches the GitHub Action that generates an Operating Brief draft.
- `/api/preview/[token]/send` - sends the Supabase `draft` Operating Brief to active subscribers.

## Local Development

Install dependencies:

```bash
npm install
```

Run the app:

```bash
npm run dev
```

Open `http://localhost:3000`.

When using `/admin`, also run the root preview file server if you want "Open preview" to work:

```bash
cd ..
python3 serve.py
```

The admin opens preview HTML from `http://localhost:8765`.

## Environment

The website expects:

- `NEXT_PUBLIC_SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `RESEND_API_KEY`
- `ADMIN_PASSWORD`
- `PREVIEW_TOKEN`
- `GITHUB_PAT` if `/preview/[token]/generate` should trigger GitHub Actions

Do not commit `.env.local` or `.env.production`.

## Design Notes

The website should match the newsletter style: white editorial surfaces, black/grey typography, ruled lines, no gradients, no rounded marketing cards, and minimal colour. Keep changes aligned with `../STYLE_GUIDE.md`.

The site is support infrastructure for the email products. Avoid turning public pages into broad marketing landing pages unless the product direction changes.
