-- Run this in your Supabase SQL editor to set up The Paddock Brief tables.
-- Mirrors the structure of the existing Operating Brief and Sporting Brief tables.

-- Subscribers for The Paddock Brief
create table if not exists paddock_subscribers (
  id         uuid primary key default gen_random_uuid(),
  email      text unique not null,
  token      text unique not null default gen_random_uuid()::text,
  active     boolean not null default true,
  created_at timestamptz not null default now()
);

-- Edition archive — one row per send
create table if not exists paddock_editions (
  id           uuid primary key default gen_random_uuid(),
  slug         text unique not null,  -- e.g. '2026-05-05'
  subject      text not null,
  preview_text text,
  html         text not null,
  created_at   timestamptz not null default now()
);

-- Send log
create table if not exists paddock_send_log (
  id               uuid primary key default gen_random_uuid(),
  subject          text not null,
  recipient_count  int not null default 0,
  resend_id        text,
  sent_at          timestamptz not null default now()
);

-- RLS
alter table paddock_subscribers enable row level security;
alter table paddock_editions enable row level security;
alter table paddock_send_log enable row level security;

-- Anyone can subscribe
create policy "public can subscribe to paddock brief"
  on paddock_subscribers for insert
  with check (true);

-- No public read on subscriber list
create policy "no public read on paddock subscribers"
  on paddock_subscribers for select
  using (false);

-- Anyone can read the edition archive
create policy "public can read paddock editions"
  on paddock_editions for select
  using (true);

-- Only service role can write editions
create policy "service role can insert paddock editions"
  on paddock_editions for insert
  with check (auth.role() = 'service_role');

create policy "service role can upsert paddock editions"
  on paddock_editions for update
  using (auth.role() = 'service_role');
