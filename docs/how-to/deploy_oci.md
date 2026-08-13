# 🛠️ Guia Prático: Implantação e Deploy na Oracle Cloud (OCI)

Este guia prático ensina passo a passo como provisionar e implantar o ecossistema do **Gêmeo Digital IoT** em uma instância de máquina virtual (VM) na **Oracle Cloud Infrastructure (OCI)** utilizando a faixa gratuita (*Always Free*) e contêineres Docker.

---

## 📋 Pré-requisitos
* Conta ativa na **Oracle Cloud Infrastructure (OCI)**.
* Chave SSH pública e privada geradas em sua máquina local (`.key` e `.key.pub`).
* Conhecimento básico em comandos Linux no terminal SSH.

---

## 🌐 1. Configuração da Rede Virtual (VCN)

Para permitir a comunicação do Nginx (Porta `8080`), FastAPI e QGIS Server com a internet:

1. No painel OCI, vá para **Networking > Virtual Cloud Networks**.
2. Clique em **Start VCN Wizard** > selecione **Create VCN with Internet Connectivity**.
3. **Nome da VCN:** `vcn-project`.
4. Mantenha os blocos de IP padrão:
   - **VCN CIDR:** `10.0.0.0/16`
   - **Sub-rede Pública:** `10.0.0.0/24`
   - **Sub-rede Privada:** `10.0.1.0/24`
5. Conclua o assistente para criar o *Internet Gateway* e as *Route Tables*.

---

## 🖥️ 2. Provisionamento da Instância Compute (VM)

1. Vá para **Compute > Instances** e clique em **Create Instance**.
2. **Nome:** `digital-twin-vm`.
3. **Imagem:** `Canonical Ubuntu 24.04 LTS` (x86_64).
4. **Formato (Shape):** `VM.Standard.E2.1.Micro` (AMD EPYC, 1 OCPU, 1 GB RAM - Always Free).
5. **Rede:** Selecione a sub-rede pública `public subnet-vcn-project` e marque **Assign a public IPv4 address**.
6. **Chave SSH:** Faça upload do seu arquivo de chave pública (ex: `ssh-key-2026-06-26.key.pub`).
7. Clique em **Create**.

---

## 🔧 3. Preparação do Servidor Ubuntu & SWAP de 4GB

Acesse a VM via SSH:

```bash
ssh -i "caminho/para/ssh-key.key" ubuntu@<IP_PUBLICO_DA_VM>
```

### A. Otimização de Memória Virtual (SWAP 4GB)
Como a instância *Micro* possui 1GB de RAM física, a criação de 4GB de SWAP é essencial para evitar falhas por falta de memória (*Out-Of-Memory / OOM*) na renderização cartográfica do QGIS:

```bash
# 1. Alocar arquivo de 4GB
sudo fallocate -l 4G /swapfile

# 2. Definir permissões de segurança
sudo chmod 600 /swapfile

# 3. Formatar e ativar
sudo mkswap /swapfile
sudo swapon /swapfile

# 4. Tornar permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 5. Confirmar memória disponível
free -h
```

### B. Instalar Docker e Docker Compose
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker Engine
sudo apt install docker.io -y
sudo usermod -aG docker ubuntu

# Instalar plugin Docker Compose v2
sudo apt install docker-compose-v2 -y
```

*(Faça logout e login novamente no SSH para atualizar as permissões do grupo `docker`).*

---

## 🚀 4. Deploy da Aplicação Gêmeo Digital

1. Clone o repositório na VM:
   ```bash
   git clone https://github.com/Falc01/digital_twins.git
   cd digital_twins
   ```
2. Inicialize o Docker Compose em modo desanexado (*daemon*):
   ```bash
   docker compose up -d
   ```
3. Verifique a saúde dos 5 contêineres:
   ```bash
   docker compose ps
   ```

---

## 🔓 5. Liberação de Portas no Firewall (Security List & iptables)

### A. Painel da Oracle Cloud
1. Acesse **Networking > VCNs > vcn-project > Security Lists > Default Security List**.
2. Clique em **Add Ingress Rules**:
   - **Source CIDR:** `0.0.0.0/0`
   - **IP Protocol:** TCP
   - **Destination Port Range:** `8080`

### B. Firewall Nativo do Ubuntu (`iptables`)
O Ubuntu na OCI vem com regras estritas de firewall local. Execute no terminal SSH:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8080 -j ACCEPT
sudo netfilter-persistent save
```

Pronto! A aplicação estará acessível publicamente em:
👉 **`http://<IP_PUBLICO_DA_VM>:8080`**

---

## 📊 6. Manutenção & Monitoramento

- **Ver logs em tempo real:** `docker compose logs -f`
- **Reiniciar os serviços:** `docker compose restart`
- **Atualizar a versão (Deploy Contínuo):**
  ```bash
  git pull origin main
  docker compose up -d --build
  ```
