import http from 'node:http';
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import pg from 'pg';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dataDir = path.join(path.dirname(fileURLToPath(import.meta.url)), 'data');
const dbPath = path.join(dataDir, 'hubvision.json');
const envPath = path.join(path.dirname(fileURLToPath(import.meta.url)), '.env');
const sessions = new Map();

try {
  const env = await fs.readFile(envPath, 'utf8');
  env.split(/\r?\n/).forEach((line) => {
    const match = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (match && !process.env[match[1]]) process.env[match[1]] = match[2].replace(/^['"]|['"]$/g, '');
  });
} catch {
  // Hosting platforms can provide environment variables directly.
}

const port = Number(process.env.PORT || 8787);
const adminEmail = (process.env.HUBVISION_ADMIN_EMAIL || 'diogogg27@gmail.com').toLowerCase();
const pool = process.env.DATABASE_URL
  ? new pg.Pool({ connectionString: process.env.DATABASE_URL, ssl: process.env.DATABASE_SSL === 'true' ? { rejectUnauthorized: false } : undefined })
  : null;

const databaseReady = pool
  ? pool.query(`
      CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        plan TEXT NOT NULL DEFAULT 'free',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        subscription_id TEXT,
        subscription_status TEXT
      )
    `)
  : Promise.resolve();

async function readDb() {
  if (pool) {
    await databaseReady;
    const result = await pool.query('SELECT email, password, plan, created_at, subscription_id, subscription_status FROM users ORDER BY created_at ASC');
    return {
      users: result.rows.map((user) => ({
        email: user.email,
        password: user.password,
        plan: user.plan,
        createdAt: user.created_at.toISOString(),
        ...(user.subscription_id ? { subscriptionId: user.subscription_id } : {}),
        ...(user.subscription_status ? { subscriptionStatus: user.subscription_status } : {})
      }))
    };
  }
  try { return JSON.parse(await fs.readFile(dbPath, 'utf8')); }
  catch { return { users: [] }; }
}

async function writeDb(db) {
  if (pool) {
    await databaseReady;
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      await client.query('DELETE FROM users');
      for (const user of db.users) {
        await client.query(
          `INSERT INTO users (email, password, plan, created_at, subscription_id, subscription_status)
           VALUES ($1, $2, $3, $4, $5, $6)`,
          [user.email, user.password, user.plan || 'free', user.createdAt || new Date().toISOString(), user.subscriptionId || null, user.subscriptionStatus || null]
        );
      }
      await client.query('COMMIT');
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
    return;
  }
  await fs.mkdir(dataDir, { recursive: true });
  await fs.writeFile(dbPath, JSON.stringify(db, null, 2));
}

function json(res, status, body) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(JSON.stringify(body));
}

function hashPassword(password, salt = crypto.randomBytes(16).toString('hex')) {
  return new Promise((resolve, reject) => crypto.scrypt(password, salt, 64, (error, key) => error ? reject(error) : resolve(`${salt}:${key.toString('hex')}`)));
}

async function verifyPassword(password, stored) {
  const [salt, expected] = stored.split(':');
  const actual = (await hashPassword(password, salt)).split(':')[1];
  return crypto.timingSafeEqual(Buffer.from(actual, 'hex'), Buffer.from(expected, 'hex'));
}

function sessionUser(req, db) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  const email = token && sessions.get(token);
  return email ? db.users.find((user) => user.email === email) : null;
}

function publicUser(user) {
  return { email: user.email, plan: user.plan, isAdmin: user.email === adminEmail };
}

async function body(req) {
  let raw = '';
  for await (const chunk of req) raw += chunk;
  return raw ? JSON.parse(raw) : {};
}

async function api(req, res) {
  try {
    const db = await readDb();
    if (req.method === 'GET' && req.url === '/api/healthz') return json(res, 200, { ok: true });
    if (req.method === 'POST' && req.url === '/api/auth/signup') {
      const { email, password } = await body(req);
      if (!email || !password || password.length < 8) return json(res, 400, { error: 'E-mail e senha de no minimo 8 caracteres sao obrigatorios.' });
      if (db.users.some((user) => user.email === email.toLowerCase())) return json(res, 409, { error: 'Este e-mail ja possui uma conta.' });
      const user = { email: email.toLowerCase(), password: await hashPassword(password), plan: 'free', createdAt: new Date().toISOString() };
      db.users.push(user);
      await writeDb(db);
      const token = crypto.randomBytes(32).toString('hex');
      sessions.set(token, user.email);
       return json(res, 201, { token, user: publicUser(user) });
    }

    if (req.method === 'POST' && req.url === '/api/auth/login') {
      const { email, password } = await body(req);
      const user = db.users.find((item) => item.email === String(email).toLowerCase());
      if (!user || !(await verifyPassword(password || '', user.password))) return json(res, 401, { error: 'E-mail ou senha invalidos.' });
      const token = crypto.randomBytes(32).toString('hex');
      sessions.set(token, user.email);
       return json(res, 200, { token, user: publicUser(user) });
    }

    if (req.method === 'GET' && req.url === '/api/auth/me') {
      const user = sessionUser(req, db);
       return user ? json(res, 200, { user: publicUser(user) }) : json(res, 401, { error: 'Sessao expirada.' });
    }

    if (req.method === 'POST' && req.url === '/api/billing/checkout') {
      const user = sessionUser(req, db);
      if (!user) return json(res, 401, { error: 'Entre para iniciar a assinatura.' });
      if (!process.env.MERCADOPAGO_ACCESS_TOKEN) return json(res, 503, { error: 'Mercado Pago ainda nao foi configurado no servidor.' });
      const configuredBackUrl = process.env.MERCADOPAGO_BACK_URL || '';
      const backUrl = configuredBackUrl.startsWith('https://') && !configuredBackUrl.includes('localhost')
        ? configuredBackUrl
        : 'https://hubvisionb.com.br/';
      const response = await fetch('https://api.mercadopago.com/preapproval', {
        method: 'POST',
        headers: { authorization: `Bearer ${process.env.MERCADOPAGO_ACCESS_TOKEN}`, 'content-type': 'application/json' },
        body: JSON.stringify({
          reason: 'HubVision Pro',
          external_reference: user.email,
          back_url: backUrl,
          notification_url: process.env.MERCADOPAGO_WEBHOOK_URL || 'https://hubvisionb.com.br/api/billing/webhook',
          auto_recurring: { frequency: 1, frequency_type: 'months', transaction_amount: Number(process.env.MERCADOPAGO_MONTHLY_PRICE || 24.9), currency_id: 'BRL' }
        })
      });
      const result = await response.json();
      console.log('Mercado Pago response:', JSON.stringify(result));
      return json(res, response.ok ? 200 : response.status, response.ok ? { checkoutUrl: result.init_point } : { error: result.message || 'Falha ao criar assinatura.', details: result });
    }

    if (req.method === 'POST' && req.url.startsWith('/api/billing/webhook')) {
      const payload = await body(req);
      const subscriptionId = payload.data?.id || new URL(req.url, 'http://localhost').searchParams.get('id');
      if (!subscriptionId || !process.env.MERCADOPAGO_ACCESS_TOKEN) return json(res, 200, { received: true });
      const response = await fetch(`https://api.mercadopago.com/preapproval/${subscriptionId}`, { headers: { authorization: `Bearer ${process.env.MERCADOPAGO_ACCESS_TOKEN}` } });
      if (!response.ok) return json(res, 200, { received: true });
      const subscription = await response.json();
      const user = db.users.find((item) => item.email === subscription.external_reference || item.email === subscription.payer_email);
      if (user) {
        user.plan = subscription.status === 'authorized' ? 'premium' : 'free';
        user.subscriptionId = String(subscription.id);
        user.subscriptionStatus = subscription.status;
        await writeDb(db);
      }
      return json(res, 200, { received: true });
    }
  } catch (error) {
    return json(res, 500, { error: 'Nao foi possivel concluir a operacao.' });
  }
  return json(res, 404, { error: 'Rota nao encontrada.' });
}

function contentType(file) {
  return { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ico': 'image/x-icon' }[path.extname(file)] || 'application/octet-stream';
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'GET' && req.url === '/healthz') return json(res, 200, { ok: true });
  if (req.url.startsWith('/api/')) return api(req, res);
  const requested = decodeURIComponent(req.url.split('?')[0]);
  const file = path.resolve(root, `.${requested === '/' ? '/index.html' : requested}`);
  if (!file.startsWith(root)) return json(res, 403, { error: 'Acesso negado.' });
  try { res.writeHead(200, { 'content-type': contentType(file) }); res.end(await fs.readFile(file)); }
  catch { json(res, 404, { error: 'Arquivo nao encontrado.' }); }
});

server.listen(port, () => console.log(`HubVision em http://localhost:${port}`));
