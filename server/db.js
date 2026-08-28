// ============================================================
// HubVision — Banco de dados (Supabase / Postgres)
// Camada de acesso aos dados usada pelo server.js.
// Usa o seu Postgres Supabase configurado em SUPABASE_URL e
// SUPABASE_SERVICE_ROLE_KEY (do .env). Se ausentes, cai no
// JSON local (fallback) para nao quebrar o desenvolvimento.
// ============================================================
import { createClient } from '@supabase/supabase-js';

const url = process.env.SUPABASE_URL || '';
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
const anonKey = process.env.SUPABASE_ANON_KEY || '';

// Cliente com service_role (acesso total ao banco, bypass RLS).
// Usado no servidor para auth/assinaturas. NUNCA expor ao front.
export const supabase = url && serviceKey ? createClient(url, serviceKey, { auth: { persistSession: false } }) : null;

export function supabaseReady() {
  return !!supabase;
}

// ------------------------------------------------------------
// USUÁRIOS
// ------------------------------------------------------------
export async function getUsers() {
  if (!supabase) return null;
  const { data, error } = await supabase.from('users').select('*').order('created_at', { ascending: true });
  if (error) throw new Error(error.message);
  return data.map((u) => ({
    email: u.email,
    password: u.password,
    plan: u.plan,
    isAdmin: !!u.is_admin,
    createdAt: u.created_at,
    subscriptionId: u.subscription_id || undefined,
    subscriptionStatus: u.subscription_status || undefined,
    id: u.id,
  }));
}

export async function findUserByEmail(email) {
  if (!supabase) return null;
  const { data } = await supabase.from('users').select('*').eq('email', String(email).toLowerCase()).maybeSingle();
  return data || null;
}

export async function createUser(email, password) {
  if (!supabase) throw new Error('Supabase não configurado.');
  const { data, error } = await supabase.from('users').insert({ email: String(email).toLowerCase(), password }).select().single();
  if (error) throw new Error(error.message);
  return data;
}

export async function updateUserPlan(email, plan, subscription) {
  if (!supabase) throw new Error('Supabase não configurado.');
  const patch = { plan, updated_at: new Date().toISOString() };
  if (subscription?.id) patch.subscription_id = String(subscription.id);
  if (subscription?.status) patch.subscription_status = subscription.status;
  const { error } = await supabase.from('users').update(patch).eq('email', String(email).toLowerCase());
  if (error) throw new Error(error.message);
}

// ------------------------------------------------------------
// ASSINATURAS (Mercado Pago)
// ------------------------------------------------------------
export async function upsertSubscription(userEmail, mp) {
  if (!supabase) return;
  const user = await findUserByEmail(userEmail);
  if (!user) return;
  const row = {
    user_id: user.id,
    mercado_pago_id: String(mp.id),
    status: mp.status === 'authorized' ? 'authorized' : 'pending',
    plan: 'premium',
    amount: Number(process.env.MERCADOPAGO_MONTHLY_PRICE || 24.9),
    currency: 'BRL',
    updated_at: new Date().toISOString(),
  };
  const { error } = await supabase.from('subscriptions').upsert(row, { onConflict: 'mercado_pago_id' });
  if (error) console.error('upsert subscriptão:', error.message);
}

// ------------------------------------------------------------
// CONTEÚDO (para crescer a biblioteca dinamicamente)
// ------------------------------------------------------------
export async function getCategories() {
  if (!supabase) return [];
  const { data, error } = await supabase.from('categories').select('*').eq('is_active', true).order('sort_order', { ascending: true });
  if (error) throw new Error(error.message);
  return data || [];
}

export async function getPrompts({ category, model, limit = 200 } = {}) {
  if (!supabase) return [];
  let q = supabase.from('prompts').select('*').limit(limit).order('created_at', { ascending: false });
  if (category) q = q.eq('category_id', category);
  if (model) q = q.eq('model', model);
  const { data, error } = await q;
  if (error) throw new Error(error.message);
  return data || [];
}

export async function getTools({ category, limit = 500 } = {}) {
  if (!supabase) return [];
  let q = supabase.from('tools').select('*').limit(limit).order('created_at', { ascending: false });
  if (category) q = q.eq('category_id', category);
  const { data, error } = await q;
  if (error) throw new Error(error.message);
  return data || [];
}
