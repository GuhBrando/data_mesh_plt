# Skill `provision-infra` — Design

## Objetivo

Skill de projeto do Claude Code que guia o provisionamento completo da infra do
Data Mesh Platform **partindo do zero**, orquestrando os stacks Terraform na ordem
correta e parando nos gates manuais. Enxuta: referencia `infra/terraform/README.md`
como fonte da verdade em vez de duplicar conteúdo.

## Modo de operação

Walkthrough guiado: Claude roda os comandos `terraform`/`az`/`databricks` por fases,
coleta inputs, valida cada `plan` antes do `apply`, e pausa nos gates manuais.

## Escopo

Só infra Terraform. Deploy das apps continua via GitHub Actions (`cd.yml`).

## Fluxo (6 fases sequenciais, com checkpoints)

| Fase | Ação | Gate manual |
|------|------|-------------|
| 0 | Checar CLIs (`az`, `terraform`, `databricks`, `jq`), `az login`, coletar `subscription_id`/`tenant_id`/`databricks_account_id` | — |
| 1 | `bootstrap/` → cria storage do remote state (state local) | — |
| 2 | `platform/` → init, import condicional, `plan` (zero destroy/replace), `apply` | identidade Owner/UAA para role assignments |
| 3 | `databricks_bootstrap/` → registra `dmplt-admin`; depois account-admin | toggle "Account admin" no console OU `grant-account-admin.sh` |
| 4 | `data_plane/` → metastore + catálogos + grants | — |
| 5 | (opcional) `grant-read-all-users.sh` | — |

## Princípios

- **Idempotente/reentrante:** cada fase detecta se já foi concluída e pula com
  segurança, permitindo retomar de onde parou.
- **README como fonte da verdade:** SKILL.md aponta para
  `infra/terraform/README.md` para detalhes longos.
- **Para nos gates:** fases 2 e 3 exigem confirmação da pré-condição antes de seguir.

## Estrutura de arquivos

- `.claude/skills/provision-infra/SKILL.md` — único arquivo, enxuto.

## Pré-requisitos não auto-instalados

A skill verifica e aponta como instalar CLIs faltantes, mas não auto-instala
(evita ação invasiva no ambiente do usuário).
