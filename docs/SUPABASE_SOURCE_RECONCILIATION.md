# Reconciliação do código Edge

> **Registro histórico (2026-09-13).** **Revisado em:** 2026-10-24 · **Base verificada:** `5f482ce1`.
> O projeto `Tradutor IA Community` citado abaixo deixou de ser o backend ativo no cutover de
> 2026-09-29 (commit `8b0053fe`, `config/public-runtime.json`); hoje é apenas rollback
> temporário. Ver [SUPABASE_AUTH.md](SUPABASE_AUTH.md). Os seis entrypoints continuam em
> `supabase/functions/`; não há verificação, nesta revisão, de que o projeto ativo execute a
> mesma versão.

Em 2026-09-13, o código local das funções necessárias à primeira closed beta
foi comparado com o código ativo no projeto Supabase `Tradutor IA Community`.
Os seis entrypoints abaixo foram incorporados do remoto após revisão:

- `beta-bootstrap` (versão remota 8)
- `device-challenge` (versão remota 8)
- `device-register` (versão remota 8)
- `device-verify` (versão remota 8)
- `device-heartbeat` (versão remota 8)
- `translation-execute` (versão remota 11)

Os entrypoints locais agora correspondem ao conteúdo ativo consultado. As
funções continuam com `verify_jwt=true`, exigem autenticação e falham fechado
quando a configuração ou autorização não está disponível.

Nenhum secret, dado de usuário, migration ou registro remoto foi alterado.
As chaves de serviço e a chave DeepL permanecem exclusivamente na configuração
do backend; a reconciliação não constitui um deploy.
