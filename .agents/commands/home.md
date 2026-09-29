---
name: home
description: Reseta a sessão do Atlas para o estado neutro e exibe o Hub Central com o Painel dos Supervisores, Downloads, Cofre de Ideias Roteado (/idea [projeto]) e Diagnóstico do Sistema.
---

# /home — Hub Central e Estado Neutro do Atlas

## Instruções
Ao receber o comando `/home`, o Atlas executa o script `scripts/home.py` para sincronizar os dados e apresenta o **Painel Central de Governança**:

1. **🔍 Verificação e Status dos Supervisores**: Estado real sincronizado de cada repositório;
2. **⏳ Projetos Pendentes de Supervisor**: Lista de projetos ativos sem supervisor;
3. **💡 Sistema de Ideias Roteado (`/idea`)**:
   - `/idea` ou `/ideias`: Visão geral do Cofre Global + Contadores por projeto;
   - `/idea [projeto]` ou `/ideias_[projeto]`: Fetch direto das ideias de um projeto específico;
   - `/idea [texto da ideia]`: Auto-roteamento para o projeto citado ou Cofre Global;
4. **📥 Verificação da Pasta Downloads**: Inspeção do Inbox oficial de arquivos soltos;
5. **🧠 Diagnóstico de Saúde do Sistema ATLAS**: Avaliação de poluição de contexto e recomendação de reset;
6. **📊 Métricas & Contadores do Ecossistema**: Estatísticas de Rules, Skills, Scripts, Commands e Hooks criados pelo sistema.
