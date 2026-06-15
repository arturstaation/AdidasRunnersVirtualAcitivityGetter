# Deploy via Ansible — Adidas Runners (isolado)

Projeto Ansible **próprio do Adidas**, no estilo da Florae mas **totalmente separado**
(inventário, playbook e **vault próprios**). Não toca em `Florae.Infra`, no vault da
Florae nem em nada do cluster deles — só usa o binário `ansible` que já está na VM.

O que o playbook faz (idempotente), tudo no host:
1. Renderiza o `.env` do stack a partir do **vault cifrado** (secrets nunca em texto puro no disco-fonte).
2. `docker compose build bot` — build **arm64 nativo** na VM.
3. Sobe o Postgres dedicado `adidas-db` e espera ficar pronto.
4. Instala e ativa o **systemd timer** (a cada 6h).
5. Com `-e run_now=true`, executa o bot **uma vez** (validação/cutover).

## Uso (na VM, control node = a própria VM)

```bash
# 1. clonar o repo na VM (já como opc)
git clone https://github.com/arturstaation/AdidasRunnersVirtualAcitivityGetter.git ~/adidas-runners
cd ~/adidas-runners/infrastructure/ansible

# 2. dependências do Ansible (uma vez)
ansible-galaxy collection install community.docker ansible.posix

# 3. criar o vault próprio (separado do da Florae)
cp group_vars/vault.example.yml group_vars/vault.yml
nano group_vars/vault.yml            # PG_PASSWORD, TOKEN, CHAT_ID, ADMIN_CHAT_ID
ansible-vault encrypt group_vars/vault.yml

# 4. deploy + run de validação
ansible-playbook site.yml --ask-vault-pass -e run_now=true
```

Depois disso o timer cuida das execuções de 6h em 6h. Para só atualizar (sem run):
```bash
ansible-playbook site.yml --ask-vault-pass
```

## Isolamento
- **Vault próprio** (`group_vars/vault.yml`), com sua própria senha — nada a ver com o
  `VAULT_PASSWORD` da Florae.
- Inventário `inventory.local.ini` aponta para `localhost` (a VM), grupo `[adidas]`.
- Opera só sobre `../host` (compose + `.env` + units do stack Adidas). Não roda nenhum
  role da Florae.

## Alternativa sem Ansible
O `../host/deploy.sh` faz o mesmo com um `.env` na mão (sem vault). Use o que preferir;
os dois compartilham o mesmo `docker-compose.yml` e units.

## CI
O workflow continua subindo por SSH e chamando `deploy.sh` (simples, sem precisar da
senha do vault no GitHub). Se quiser que o CI rode o **Ansible**, basta adicionar um
secret com a senha do vault (modelo `VAULT_PASSWORD` da Florae) e trocar o passo de
deploy por `ansible-playbook ... --vault-password-file`.
