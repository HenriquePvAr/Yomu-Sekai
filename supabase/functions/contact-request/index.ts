// "Solicitar fonte" and feedback from the app: stored by submit_contact_request, then
// e-mailed to the team inbox through Resend. The inbox and the API key are function
// secrets (CONTACT_INBOX_EMAIL, RESEND_API_KEY), never in the repository.
import { json, preflight } from "../_shared/http.ts";
import { requireAuth } from "../_shared/auth.ts";
import { callRpc } from "../_shared/rpc.ts";

const SUBJECTS: Record<string, string> = {
  source_request: "Nova fonte solicitada",
  feedback: "Novo feedback",
};

const escapeHtml = (value: unknown) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));

function emailHtml(kind: string, who: string, email: string, url: string, message: string): string {
  const row = (label: string, value: string) => value
    ? `<tr><td style="padding:10px 0;color:#8a8377;font:11px/1.4 monospace;letter-spacing:.1em;text-transform:uppercase;width:120px;vertical-align:top">${label}</td>`
      + `<td style="padding:10px 0;color:#efe7d8;font:15px/1.5 Arial,sans-serif;word-break:break-word">${value}</td></tr>`
    : "";
  return `<!doctype html><html><body style="margin:0;background:#0c0c0f;padding:32px 16px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#17161b;border:1px solid #2c2a30">
<tr><td style="height:4px;background:#c5372c"></td></tr>
<tr><td style="padding:28px 32px 8px;font:700 22px Arial,sans-serif;color:#efe7d8">YOMU <span style="color:#c5372c">SEKAI</span></td></tr>
<tr><td style="padding:0 32px 20px;color:#c9a227;font:11px monospace;letter-spacing:.14em;text-transform:uppercase">${escapeHtml(SUBJECTS[kind])}</td></tr>
<tr><td style="padding:0 32px 24px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #2c2a30">
${row("Enviado por", escapeHtml(who))}${row("E-mail", escapeHtml(email))}
${row("Fonte", url ? `<a href="${escapeHtml(url)}" style="color:#e0c981">${escapeHtml(url)}</a>` : "")}
${row(kind === "feedback" ? "Mensagem" : "Observação", escapeHtml(message).replace(/\n/g, "<br>"))}
</table></td></tr>
<tr><td style="padding:16px 32px;border-top:1px solid #2c2a30;color:#8a8377;font:12px Arial,sans-serif">Enviado pelo aplicativo Yomu Sekai.</td></tr>
</table></td></tr></table></body></html>`;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return preflight();
  const denied = requireAuth(req);
  if (denied) return denied;
  let body: any;
  try { body = await req.json(); } catch { return json({ code: "invalid_json" }, 400); }
  const kind = String(body?.kind || "");
  const url = String(body?.url || "").trim();
  const message = String(body?.message || "").trim();
  if (!SUBJECTS[kind]) return json({ code: "invalid_kind" }, 400);
  if (kind === "source_request" && (!/^https?:\/\/[^\s]+\.[^\s]+/i.test(url) || url.length > 500)) {
    return json({ code: "invalid_url" }, 400);
  }
  if (kind === "feedback" && (message.length < 3 || message.length > 2000)) return json({ code: "invalid_message" }, 400);
  if (message.length > 2000) return json({ code: "invalid_message" }, 400);

  const stored = await callRpc(req, "submit_contact_request", {
    p_kind: kind, p_url: kind === "source_request" ? url : null, p_message: message || null,
  });
  if (stored.error) return json({ code: stored.error }, 503);
  if (!stored.response!.ok) {
    const limited = String(stored.payload?.message || "").includes("rate_limited");
    return json({ code: limited ? "rate_limited" : "contact_store_failed" }, limited ? 429 : 409);
  }
  const identity = stored.payload || {};
  const who = identity.display_name || identity.username || "Usuário sem nome";

  const apiKey = Deno.env.get("RESEND_API_KEY");
  const inbox = Deno.env.get("CONTACT_INBOX_EMAIL");
  if (!apiKey || !inbox) return json({ ok: true, delivered: false, code: "mail_not_configured" });
  try {
    const sent = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
      body: JSON.stringify({
        from: Deno.env.get("CONTACT_FROM_EMAIL") || "Yomu Sekai <onboarding@resend.dev>",
        to: [inbox],
        reply_to: identity.email || undefined,
        subject: `${SUBJECTS[kind]} · ${who}`,
        html: emailHtml(kind, who, identity.email || "", kind === "source_request" ? url : "", message),
      }),
    });
    return json({ ok: true, delivered: sent.ok });
  } catch {
    return json({ ok: true, delivered: false, code: "mail_send_failed" });
  }
});
