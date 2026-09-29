# Rule: Painel de Standby e Sincronização Prévia dos Supervisores

## 1. Protocolo de Sincronização Prévia Obrigatória
- Antes de apresentar o Painel de Standby ou responder sobre os próximos passos dos projetos:
  - O Atlas DEVE obrigatoriamente ler/sincronizar os arquivos locais de memória viva (`.agents/memory/activeContext.md` e `progress.md`) de cada projeto contratado no disco.
  - Isso garante que a situação real de cada projeto seja refletida sem informações defasadas.

## 2. Definição do Estado Padrão de Aguardo
- Sempre que o João pedir para o Atlas "voltar ao estado padrão", "aguardar futuras interações" ou encerrar um ciclo:
  - O Atlas DEVE apresentar o **Painel Geral de Estado dos Supervisores e Projetos**:
    1. 📊 **O que já foi feito / Contratado**: Lista dos projetos ativos sincronizada com a memória local real.
    2. ⏳ **O que falta fazer / Pendente**: Lista dos projetos aguardando onboarding ou próximas etapas.

## 3. Apresentação Executiva
- O painel deve ser apresentado de forma limpa, direta e sem verborragia, mantendo o usuário 100% ciente da situação atual do ecossistema.
