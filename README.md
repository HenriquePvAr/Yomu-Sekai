# Komyst

Pipeline local para traduzir capítulos ilustrados para português brasileiro. O Komyst coleta
as páginas, reconhece e classifica o texto, solicita a tradução ao backend autenticado,
reconstrói as imagens e gera um PDF. Regiões com qualidade incerta podem exigir revisão.

> Beta técnica. O ambiente documentado é Windows 64 bits com Python 3.11. Os requisitos
> mínimos ainda não foram homologados. Veja [limitações e estado do produto](docs/KNOWN_ISSUES.md)
> antes de usar.

## Começar

Baixe o instalador da versão Beta disponibilizada pela equipe, execute `Komyst-0.9.1-beta.18-Setup-x64.exe`
e abra o Komyst pelo atalho criado. Entre com sua conta e a licença Beta fornecida pela equipe.
O instalador e a instalação limpa dessa versão foram **validados por beta tester, informado pelo dono**;
a data dessa rodada não foi informada. Consulte o [Guia do Usuário](docs/user/GUIA_DO_USUARIO.md)
para o primeiro acesso e a [documentação de instalação](docs/INSTALLATION.md) para detalhes técnicos.

## Desenvolvimento

Para preparar o ambiente de desenvolvimento no Windows:

```powershell
git clone --branch dev https://github.com/HenriquePvAr/Komyst.git
cd Komyst
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -s -m pip install -r requirements/requirements-beta.txt
Copy-Item .env.example .env
```

Configure `SUPABASE_URL` e `SUPABASE_PUBLISHABLE_KEY` no `.env` para autenticação e tradução.
São configurações publicáveis do cliente; **não coloque segredos de servidor nesse arquivo**.
Inicie worker e interface juntos:

```powershell
python start_tradutor.py
```

Abra `http://127.0.0.1:8080`. O login está configurado para essa origem. Consulte também
[Configuração](docs/CONFIGURATION.md) e [Desenvolvimento](docs/DEVELOPMENT.md).

## O que o aplicativo oferece

- Entrada por URL de fontes com adapter e por pasta local. A análise universal de uma URL não
  garante que o site seja compatível.
- OCR, tradução autenticada via backend e validações de texto e imagem.
- Modos **Qualidade** e **Download-only** na interface.
- Saídas **Tradução pronta**, **Apenas Clean**, **Completo**, **Apenas tradução**,
  **Tradução + Clean** e opções personalizadas. **Apenas download** fica no modo de
  processamento. Os detalhes de cada escolha estão em [Modos de saída](docs/product/output_modes.md).
- Fila local persistente e histórico de execuções.

Uma execução marcada `review_required` pode ter PDF pronto, mas contém pontos que precisam de
inspeção. Isso não equivale a uma tradução aprovada nem a uma falha técnica. Consulte
[Saídas e artefatos](docs/OUTPUT_ARTIFACTS.md) e [Qualidade e validação](docs/QUALITY_AND_VALIDATION.md).

## Estados do job

| Estado terminal | Significado |
| --- | --- |
| `finished` | Execução concluída e aprovada no quality gate |
| `review_required` | Concluída, com PDF disponível, mas com revisão de qualidade pendente |
| `failed` | Falha técnica ou artefato essencial ausente (exibido como "erro" na interface) |
| `cancelled` | Cancelamento explícito |

Há 15 estados ao todo em `komyst/runtime/job_store.py` (`JobStatus.ALL`), entre eles os
intermediários `staging`, `claiming`, `starting`, `interrupted` e `resumable`. A máquina de
estados completa está em [Documentação Técnica §8](docs/technical/DOCUMENTACAO_TECNICA.md#8-máquina-de-estados-do-job).

## Desempenho medido

Números físicos (CPU, RAM, GPU e tempo por etapa) de uma execução de referência estão em
[Perfil de hardware medido](docs/HARDWARE_PROFILE.md) — são medições de uma máquina e um
capítulo, não requisitos mínimos homologados.

## Limites conhecidos

- A Beta é voltada ao Windows; outros sistemas não fazem parte do ambiente validado.
- Tradução exige conta Komyst e conexão com os serviços configurados. A chave do DeepL fica no
  servidor; o aplicativo a acessa pelo backend autenticado.
- O resultado pode conter texto ou reconstrução visual que exija revisão humana. O sistema não
  garante tradução perfeita.
- Instalação em Windows limpo, requisitos mínimos e distribuição final ainda têm gates
  pendentes. Veja [Problemas conhecidos](docs/KNOWN_ISSUES.md).

## Documentação

Use o [índice da documentação](docs/README.md) para encontrar guias por assunto.

- [Guia do usuário](docs/user/GUIA_DO_USUARIO.md)
- [Desenvolvimento](docs/DEVELOPMENT.md) · [Arquitetura](docs/ARCHITECTURE.md)
- [Testes](docs/TESTING.md) · [Segurança](docs/SECURITY.md)
- [Contribuir](CONTRIBUTING.md)

Relatórios, auditorias e planos antigos estão preservados como histórico. Eles registram o
estado na data em que foram escritos; para comportamento atual, use primeiro os guias acima e
os documentos primários listados no índice.

## Sobre

Desenvolvido por [Henrique Araujo](https://github.com/HenriquePvAr).
