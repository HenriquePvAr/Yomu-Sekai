import { json } from "../_shared/http.ts";

// Rewarded ads are disabled: this endpoint only answers 503 and credits nothing.
// When the provider is activated, implement the callback together with its credit RPC
// (server-side only), verify the provider HMAC signature, and set
// `[functions.rewarded-ad-callback] verify_jwt = false` in supabase/config.toml, because the
// provider calls without a Supabase JWT.
Deno.serve((req) => {
  if (req.method !== "GET" && req.method !== "POST") return json({ code: "method_not_allowed" }, 405);
  return json({ code: "rewarded_ads_disabled" }, 503);
});
