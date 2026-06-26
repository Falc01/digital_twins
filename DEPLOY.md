# Guia de Implantação e Deploy do Gêmeo Digital (OCI Always Free)

Este documento detalha o processo de provisionamento da infraestrutura de rede, criação da Máquina Virtual (VM) e preparação do sistema operacional na **Oracle Cloud Infrastructure (OCI)** para o deploy do projeto Gêmeo Digital UNIFACS IoT.

---

## 1. Arquitetura de Rede (VCN - Virtual Cloud Network)

Para permitir a comunicação segura e o tráfego de dados do mapa (QGIS Server) e das requisições web (Nginx/FastAPI), criamos uma rede virtual isolada com saída para a internet.

* **Método de Criação:** Assistente de VCN com Conectividade com a Internet (*VCN Wizard - Create VCN with Internet Connectivity*).
* **Nome da VCN:** `vcn-project` (associada ao compartimento raiz do usuário).
* **Estrutura Criada de Forma Automática:**
  * **VCN CIDR:** `10.0.0.0/16` (faixa de IPs privados reservados para a rede interna).
  * **Sub-rede Pública:** `public subnet-vcn-project` (faixa de IP `10.0.0.0/24` para recursos que necessitam de IPs públicos de internet).
  * **Sub-rede Privada:** `private subnet-vcn-project` (faixa de IP `10.0.1.0/24` para recursos protegidos sem exposição direta).
  * **Internet Gateway (IG):** Canal que conecta a sub-rede pública à internet.
  * **NAT Gateway (NAT):** Permite que as instâncias da rede privada baixem atualizações na internet de forma segura.
  * **Tabela de Rotas (Route Table):** Roteamento automático das requisições da sub-rede pública para o Internet Gateway.

---

## 2. Provisionamento da Instância Compute (VM)

Criamos a máquina virtual na nuvem utilizando o plano gratuito perpétuo (*Always Free*) da Oracle Cloud, adotando o processador de arquitetura x86_64 devido à disponibilidade de estoque na região de São Paulo.

* **Nome da VM:** `digital-twin-vm`
* **Localização (Placement):** Domínio de Disponibilidade 1 (SAOPAULO-AD-1).
* **Sistema Operacional (Image):** `Canonical Ubuntu 24.04 LTS` (x86_64).
* **Formato (Shape):** `VM.Standard.E2.1.Micro` (Processador AMD EPYC, 1 OCPU, 1 GB de memória RAM).
* **Rede Vinculada:**
  * Associada à sub-rede pública `public subnet-vcn-project`.
  * **IP Público Atribuído automaticamente:** Sim.
* **Segurança e Acesso SSH:**
  * Vinculação da chave pública gerada na máquina de desenvolvimento: [ssh-key-2026-06-26.key.pub](file:///c:/Users/joaof/Downloads/Unifacs/digital_twins/ssh-key-2026-06-26.key.pub).
  * O acesso root/SSH só é permitido utilizando a respectiva chave privada: [ssh-key-2026-06-26.key](file:///c:/Users/joaof/Downloads/Unifacs/digital_twins/ssh-key-2026-06-26.key).

---

## 3. Preparação do Servidor (Passos de Deploy)

Os seguintes passos descrevem o procedimento técnico para preparar a VM de 1GB de RAM, otimizar sua memória com partição de paginação (SWAP), instalar o Docker e colocar a aplicação no ar.

### Passo 3.1: Acesso Remoto via SSH
Conectar na máquina utilizando o IP público atribuído e a chave privada baixada:
```bash
ssh -i "ssh-key-2026-06-26.key" ubuntu@<IP_PUBLICO_DA_VM>
```

### Passo 3.2: Otimização de Memória (Criação de SWAP)
Como a máquina possui 1GB de RAM física e rodará múltiplos contêineres Docker, precisamos criar uma memória virtual de **4GB** em disco para evitar travamentos de falta de memória (Out-Of-Memory/OOM):
```bash
# 1. Aloca um arquivo de 4GB para a SWAP
sudo fallocate -l 4G /swapfile

# 2. Define a permissão correta para que apenas o root acesse o arquivo
sudo chmod 600 /swapfile

# 3. Formata o arquivo como área de troca (swap)
sudo mkswap /swapfile

# 4. Ativa a memória virtual temporariamente
sudo swapon /swapfile

# 5. Adiciona a configuração ao fstab para manter ativa após reinicializações
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 6. Verifica se a memória foi ativada com sucesso
free -h
```

### Passo 3.3: Instalação do Docker e Docker Compose
Instalar o motor de contêineres para gerenciar nossos serviços:
```bash
# Atualizar a lista de pacotes e o sistema
sudo apt update && sudo apt upgrade -y

# Instalar o Docker Engine e utilitários
sudo apt install docker.io -y

# Adicionar o usuário ubuntu ao grupo docker para não precisar usar 'sudo' em todos os comandos do docker
sudo usermod -aG docker ubuntu

# Instalar o Docker Compose v2 (plugin do CLI do docker)
sudo apt install docker-compose-v2 -y
```
*(Nota: após adicionar o usuário ao grupo docker, faça logoff e login novamente no SSH para aplicar a permissão).*

### Passo 3.4: Inicialização do Gêmeo Digital
1. Clonar o projeto do repositório oficial do GitHub:
   ```bash
   git clone https://github.com/Falc01/digital_twins.git
   cd digital_twins
   ```
2. Iniciar o orquestrador Docker Compose em segundo plano (modo daemon):
   ```bash
   docker compose up -d
   ```
3. A aplicação estará ativa em:
   * **URL Pública:** `http://<IP_PUBLICO_DA_VM>:8080` (Consolidação do Nginx redirecionando para o frontend, FastAPI e QGIS Server).

---

## 4. Liberação das Portas no Painel da Oracle (Security List)

Por padrão, a Oracle bloqueia todo o tráfego externo de entrada. Para que a aplicação web na porta `8080` fique acessível no navegador de outros dispositivos, é necessário:
1. No console da Oracle, acessar a página da **VCN** (`vcn-project`).
2. Entrar em **Security Lists** (Listas de Segurança) e selecionar a **Default Security List for vcn-project**.
3. Clicar em **Add Ingress Rules** (Adicionar Regras de Entrada).
4. Configurar a nova regra:
   * **Source Type:** CIDR
   * **Source CIDR:** `0.0.0.0/0` (qualquer IP da internet)
   * **IP Protocol:** TCP
   * **Destination Port Range:** `8080` (ou `80,443` se alterar futuramente)
5. Clicar em **Add Ingress Rules**.
