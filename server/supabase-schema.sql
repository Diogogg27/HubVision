-- ============================================================
-- HubVision — Schema Supabase (Postgres)
-- Rode este script no SQL Editor do Supabase (ou via psql).
-- Cria as tabelas e políticas para a biblioteca de prompts.
-- ============================================================

-- Extensões úteis
create extension if not exists "uuid-ossp";

-- ------------------------------------------------------------
-- USUÁRIOS (substitui o server/data/hubvision.json)
-- ------------------------------------------------------------
create table if not exists public.users (
  id uuid primary key default uuid_generate_v4(),
  email text unique not null,
  password text not null,             -- hash scrypt "salt:hash"
  plan text not null default 'free',  -- 'free' | 'premium'
  is_admin boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ------------------------------------------------------------
-- ASSINATURAS (Mercado Pago preapproval)
-- ------------------------------------------------------------
create table if not exists public.subscriptions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references public.users(id) on delete cascade on update cascade,
  mercado_pago_id text,
  status text not null default 'pending',  -- pending | authorized | cancelled | paused
  plan text not null default 'premium',
  amount numeric(10,2) not null default 24.90,
  currency text not null default 'BRL',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (mercado_pago_id)
);

-- ------------------------------------------------------------
-- CONTEÚDO — CATEGORIAS (para crescer a biblioteca)
-- ------------------------------------------------------------
create table if not exists public.categories (
  id uuid primary key default uuid_generate_v4(),
  slug text unique not null,
  name text not null,
  icon text,
  description text,
  is_active boolean not null default true,
  sort_order int not null default 0,
  created_at timestamptz not null default now()
);

-- ------------------------------------------------------------
-- CONTEÚDO — PROMPTS (a biblioteca cresce aqui)
-- ------------------------------------------------------------
create table if not exists public.prompts (
  id uuid primary key default uuid_generate_v4(),
  category_id uuid references public.categories(id) on delete set null,
  title text not null,
  prompt text not null,
  model text,                       -- Midjourney, DALL-E, ChatGPT, ...
  image_url text,
  preview_url text,
  is_premium boolean not null default true, -- false = amostra gratuita
  language text not null default 'pt-BR',
  uses int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ------------------------------------------------------------
-- CONTEÚDO — FERRAMENTAS / SITES DE IA
-- ------------------------------------------------------------
create table if not exists public.tools (
  id uuid primary key default uuid_generate_v4(),
  category_id uuid references public.categories(id) on delete set null,
  name text not null,
  url text unique not null,
  description text,
  logo_url text,
  is_premium boolean not null default true,
  created_at timestamptz not null default now()
);

-- ------------------------------------------------------------
-- FAVORITOS DO USUÁRIO
-- ------------------------------------------------------------
create table if not exists public.favorites (
  user_id uuid references public.users(id) on delete cascade on update cascade,
  item_type text not null,   -- 'prompt' | 'tool'
  item_id uuid not null,
  created_at timestamptz not null default now(),
  primary key (user_id, item_type, item_id)
);

-- ------------------------------------------------------------
-- ÍNDICES
-- ------------------------------------------------------------
create index if not exists idx_users_email on public.users(email);
create index if not exists idx_prompts_category on public.prompts(category_id);
create index if not exists idx_prompts_model on public.prompts(model);
create index if not exists idx_tools_category on public.tools(category_id);
create index if not exists idx_subscriptions_user on public.subscriptions(user_id);

-- ------------------------------------------------------------
-- TRIGGERS de updated_at
-- ------------------------------------------------------------
create or replace function public.touch_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_users_touch on public.users;
create trigger trg_users_touch before update on public.users
  for each row execute function public.touch_updated_at();

drop trigger if exists trg_prompts_touch on public.prompts;
create trigger trg_prompts_touch before update on public.prompts
  for each row execute function public.touch_updated_at();

drop trigger if exists trg_subscriptions_touch on public.subscriptions;
create trigger trg_subscriptions_touch before update on public.subscriptions
  for each row execute function public.touch_updated_at();

-- ------------------------------------------------------------
-- ROW LEVEL SECURITY
-- O servidor usa a service_role (bypass RLS). Aplicamos RLS
-- defensivo: somente leitura pública para conteúdo aberto,
-- e acesso total via service_role (cookies/anon passam a ter
-- permissões adicionadas conforme evolução do app).
-- ------------------------------------------------------------
alter table public.users enable row level security;
alter table public.subscriptions enable row level security;
alter table public.favorites enable row level security;
alter table public.prompts enable row level security;
alter table public.tools enable row level security;
alter table public.categories enable row level security;

-- Conteúdo aberto (amostras) legível por todos
create policy "public read prompts" on public.prompts
  for select using (true);
create policy "public read tools" on public.tools
  for select using (true);
create policy "public read categories" on public.categories
  for select using (true);

-- Usuário só enxerga a própria conta
create policy "own users" on public.users
  for select using (auth.uid() = id);
create policy "own favorites" on public.favorites
  for all using (auth.uid() = user_id);
