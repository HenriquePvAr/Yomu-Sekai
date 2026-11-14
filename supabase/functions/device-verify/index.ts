import { json, preflight } from "../_shared/http.ts";
import { bearer, requireAuth } from "../_shared/auth.ts";

const decode = (s: string) => {
  const x = s.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(s.length / 4) * 4, '=');
  return Uint8Array.from(atob(x), c => c.charCodeAt(0));
};

export async function handleRequest(req: Request): Promise<Response> {
  if (req.method === "OPTIONS") return preflight();
  const denied = requireAuth(req);
  if (denied) return denied;
  try {
    const b: any = await req.json();
    const u = Deno.env.get('SUPABASE_URL'), k = Deno.env.get('SUPABASE_ANON_KEY'), t = bearer(req);
    if (!u || !k || !t) return json({ code: 'control_plane_not_configured' }, 503);
    const h = { apikey: k, Authorization: `Bearer ${t}`, 'content-type': 'application/json' };
    const q = await fetch(`${u}/rest/v1/rpc/get_device_challenge_for_verify`, {
      method: 'POST', headers: h, body: JSON.stringify({ p_challenge_id: b?.challenge_id })
    });
    const c: any = await q.json().catch(() => null);
    if (!q.ok || !c) return json({ code: 'device_challenge_not_found' }, 404);
    if (c.device_status !== 'active') return json({ code: 'device_revoked' }, 403);
    if (c.license_status !== 'active') return json({ code: 'license_not_active' }, 403);
    if (c.license_expires_at != null) {
      const expiresAt = typeof c.license_expires_at === 'string' ? Date.parse(c.license_expires_at) : Number.NaN;
      if (!Number.isFinite(expiresAt) || expiresAt <= Date.now()) return json({ code: 'license_not_active' }, 403);
    }
    if (c.consumed_at) return json({ code: 'device_challenge_consumed' }, 409);
    if (new Date(c.expires_at).getTime() <= Date.now()) return json({ code: 'device_challenge_expired' }, 410);
    const nonce = String(b?.nonce || '');
    const dig = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(nonce));
    const hash = Array.from(new Uint8Array(dig)).map(x => x.toString(16).padStart(2, '0')).join('');
    if (hash !== c.nonce_hash) return json({ code: 'device_challenge_invalid' }, 401);
    let key: CryptoKey;
    try {
      key = await crypto.subtle.importKey('raw', decode(String(c.public_key)), { name: 'Ed25519' }, false, ['verify']);
    } catch {
      return json({ code: 'device_signature_invalid' }, 401);
    }
    let sig: Uint8Array;
    try {
      sig = decode(String(b?.signature || ''));
    } catch {
      return json({ code: 'device_signature_invalid' }, 401);
    }
    const signatureBytes = new Uint8Array(sig).buffer as ArrayBuffer;
    const nonceBytes = new TextEncoder().encode(nonce).buffer as ArrayBuffer;
    if (!await crypto.subtle.verify({ name: 'Ed25519' }, key, signatureBytes, nonceBytes)) {
      return json({ code: 'device_signature_invalid' }, 401);
    }
    // Consumption is service_role-only: authenticated clients cannot burn a challenge
    // without passing the signature check above. The owner comes from the challenge
    // row that get_device_challenge_for_verify returned for this caller's JWT.
    const sk = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || Deno.env.get('SUPABASE_SECRET_KEY');
    if (!sk) return json({ code: 'control_plane_not_configured' }, 503);
    const consume = await fetch(`${u}/rest/v1/rpc/consume_device_challenge`, {
      method: 'POST', headers: { apikey: sk, Authorization: `Bearer ${sk}`, 'content-type': 'application/json' },
      body: JSON.stringify({ p_challenge_id: b.challenge_id, p_nonce_hash: hash, p_user_id: c.user_id })
    });
    const out = await consume.json().catch(() => ({}));
    return consume.ok ? json({ verified: true, ...out }) : json({ code: 'device_challenge_invalid' }, 409);
  } catch {
    return json({ code: 'device_verify_unavailable' }, 503);
  }
}

if (import.meta.main) Deno.serve(handleRequest);
