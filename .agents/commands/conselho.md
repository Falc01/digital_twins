---
name: conselho
description: Convoca a Sessão Formal do Conselho dos Seis Chapéus de IA para sabatinar a fundo uma proposta, decisão ou arquitetura.
---

# /conselho — Sessão Plenária do Conselho dos Seis Chapéus

## Instruções de Uso
Ao receber o comando `/conselho [proposta]`, o Atlas assume o papel de **Maestro (Chapéu Azul)** e conduz a sabatina estruturada passando individualmente pelas diretrizes modulares em `.agents/council/`:

1. **⚪ Chapéu Branco**: Audita os dados, fatos concretos, métricas e aponta lacunas de informação (`hat_white.md`).
2. **🔴 Chapéu Vermelho**: Avalia a reação visceral, atrito de uso e calor humano da experiência (`hat_red.md`).
3. **⚫ Chapéu Preto**: Ataca os gargalos, vulnerabilidades, concorrência, quebras de contrato e piores cenários (`hat_black.md`).
4. **🟡 Chapéu Amarelo**: Destaca as vantagens competitivas inegociáveis, viabilidade e retorno a longo prazo (`hat_yellow.md`).
5. **🟢 Chapéu Verde**: Desenvolve vacinas criativas contra as falhas do Chapéu Preto e atalhos laterais inteligentes (`hat_green.md`).
6. **🔵 Chapéu Azul (Veredito do Atlas / Supervisor)**: Sintetiza a decisão executiva final (Aprovado / Aprovado com Condições / Rejeitado) e entrega o checklist de implementação imediata.

## Regras de Finalização:
- Ao concluir a deliberação no chat, o Supervisor/Atlas DEVE OBRIGATORIAMENTE anexar o bloco canônico de 4 linhas da **Telemetria de Tokens** no rodapé (`atlas.token.telemetry.rule.md`).
