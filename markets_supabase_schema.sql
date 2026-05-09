-- Run this in your Supabase SQL editor to set up The Markets Brief tables.
-- Mirrors the structure of the existing Operating Brief and Sporting Brief tables.

-- Subscribers for The Markets Brief
create table if not exists markets_subscribers (
  id         uuid primary key default gen_random_uuid(),
  email      text unique not null,
  token      text unique not null default gen_random_uuid()::text,
  active     boolean not null default true,
  created_at timestamptz not null default now()
);

-- Edition archive — one row per send
create table if not exists markets_editions (
  id           uuid primary key default gen_random_uuid(),
  slug         text unique not null,  -- e.g. '2026-05-10'
  subject      text not null,
  preview_text text,
  html         text not null,
  created_at   timestamptz not null default now()
);

-- Send log
create table if not exists markets_send_log (
  id               uuid primary key default gen_random_uuid(),
  subject          text not null,
  recipient_count  int not null default 0,
  resend_id        text,
  sent_at          timestamptz not null default now()
);

-- RLS
alter table markets_subscribers enable row level security;
alter table markets_editions enable row level security;
alter table markets_send_log enable row level security;

-- Anyone can subscribe
create policy "public can subscribe to markets brief"
  on markets_subscribers for insert
  with check (true);

-- No public read on subscriber list
create policy "no public read on markets subscribers"
  on markets_subscribers for select
  using (false);

-- Anyone can read the edition archive
create policy "public can read markets editions"
  on markets_editions for select
  using (true);

-- Only service role can write
create policy "service role can insert markets editions"
  on markets_editions for insert
  with check (auth.role() = 'service_role');

create policy "service role can upsert markets editions"
  on markets_editions for update
  using (auth.role() = 'service_role');
