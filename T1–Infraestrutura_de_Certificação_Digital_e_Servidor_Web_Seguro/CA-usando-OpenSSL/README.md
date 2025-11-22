# Tarefa 2 — PKI (CA Raiz + Intermediária) e HTTPS com Nginx usando OpenSSL

* CA raiz (self-signed)
* CA intermediária (assinada pela raiz)
* Certificado de servidor (assinada pela intermediária)
* Configuração do Nginx usando esse certificado
* Importar a CA raiz no navegador para confiar no HTTPS
* Verificar a cadeia com `openssl verify` e `openssl s_client`

> Observação: os comandos abaixo assumem Linux (bash). Ajustes mínimos para macOS/Windows (ex.: caminhos, instalação do nginx) são óbvios. Substitua `nginx.example.local` pelo FQDN que usará (ou IP). Trabalharei na pasta `~/pki` como exemplo.



# 1. Layout de diretórios (inicial)

```bash
mkdir -p ~/pki/{root,intermediate,server}
cd ~/pki

# diretórios auxiliares (para CA raiz e intermediária)
mkdir -p root/{certs,crl,newcerts,private}
mkdir -p intermediate/{certs,crl,csr,newcerts,private}
touch root/index.txt root/index.txt.attr intermediate/index.txt
echo 1000 > root/serial
echo 1000 > intermediate/serial
echo 1000 > root/crlnumber
echo 1000 > intermediate/crlnumber
chmod 700 root/private intermediate/private
```



# 2. Arquivos de configuração OpenSSL (mínimos necessários)

Crie dois arquivos `root/openssl.cnf` e `intermediate/openssl.cnf`. Abaixo um exemplo enxuto — salve como indicado.

**`~/pki/root/openssl.cnf`**

```ini
[ ca ]
default_ca = CA_default

[ CA_default ]
dir               = ./                # adaptável; neste exemplo assume-se root/
certs             = $dir/certs
crl_dir           = $dir/crl
database          = $dir/index.txt
new_certs_dir     = $dir/newcerts
certificate       = $dir/certs/ca.crt
serial            = $dir/serial
crlnumber         = $dir/crlnumber
private_key       = $dir/private/ca.key
RANDFILE          = $dir/private/.rand
default_days      = 3650
default_md        = sha256
preserve          = no
policy            = policy_strict

[ policy_strict ]
commonName = supplied
countryName = optional
stateOrProvinceName = optional
organizationName = optional
organizationalUnitName = optional
emailAddress = optional

[ req ]
default_bits        = 4096
default_md          = sha256
prompt              = no
distinguished_name  = dn

[ dn ]
C = BR
ST = Sao Paulo
L = Sao Paulo
O = MinhaEmpresa
OU = PKI Root CA
CN = Minha CA Raiz (Root)

[ v3_ca ]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true, pathlen:1
keyUsage = critical, cRLSign, keyCertSign
```

**`~/pki/intermediate/openssl.cnf`**

```ini
[ ca ]
default_ca = CA_default

[ CA_default ]
dir               = ./                # neste arquivo, referir-se a intermediate/
certs             = $dir/certs
crl_dir           = $dir/crl
database          = $dir/index.txt
new_certs_dir     = $dir/newcerts
certificate       = $dir/certs/intermediate.crt
serial            = $dir/serial
crlnumber         = $dir/crlnumber
private_key       = $dir/private/intermediate.key
RANDFILE          = $dir/private/.rand
default_days      = 1825
default_md        = sha256
preserve          = no
policy            = policy_loose

[ policy_loose ]
commonName = supplied
countryName = optional
stateOrProvinceName = optional
organizationName = optional
organizationalUnitName = optional
emailAddress = optional

[ req ]
default_bits        = 4096
default_md          = sha256
prompt              = no
distinguished_name  = dn

[ dn ]
C = BR
ST = Sao Paulo
L = Sao Paulo
O = MinhaEmpresa
OU = PKI Intermediate CA
CN = Minha CA Intermediária

[ v3_intermediate_ca ]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true, pathlen:0
keyUsage = critical, cRLSign, keyCertSign
```

> `pathlen` controlará se a intermediária pode emitir outras CAs. Aqui, root tem `pathlen:1` e intermediária `pathlen:0`.



# 3. Criar CA Raiz (chave e certificado self-signed)

```bash
cd ~/pki/root

# gera chave privada da root (4096 bits)
openssl genpkey -algorithm RSA -out private/ca.key -aes256 -pass pass:senha_root -pkeyopt rsa_keygen_bits:4096
chmod 400 private/ca.key

# gera certificado autoassinado (10 anos)
openssl req -config openssl.cnf -key private/ca.key -passin pass:senha_root \
      -new -x509 -days 3650 -sha256 -extensions v3_ca -out certs/ca.crt
```

(Se preferir **sem** senha na chave, remova `-aes256` e a passagem de `-pass`.)



# 4. Criar CA Intermediária

**Gerar chave e CSR da intermediária:**

```bash
cd ~/pki/intermediate

openssl genpkey -algorithm RSA -out private/intermediate.key -aes256 -pass pass:senha_inter -pkeyopt rsa_keygen_bits:4096
chmod 400 private/intermediate.key

openssl req -config openssl.cnf -new -sha256 \
    -key private/intermediate.key -passin pass:senha_inter \
    -out csr/intermediate.csr
```

**Assinar CSR da intermediária com a CA Raiz:**

```bash
# voltar à pasta root para assinar
cd ~/pki/root
# Assinar CSR (intermediária), usando extensão v3_intermediate_ca do arquivo de intermediária.
openssl ca -config ../root/openssl.cnf -extensions v3_ca \
    -days 1825 -notext -md sha256 \
    -in ../intermediate/csr/intermediate.csr \
    -out ../intermediate/certs/intermediate.crt \
    -batch -keyfile private/ca.key -cert certs/ca.crt -passin pass:senha_root
```

Agora crie o *chain* da CA (certificado da raiz + intermediária) para conveniência:

```bash
# concatenar cadeia: intermediate -> root (usado por clientes para validação parcial)
cat intermediate/certs/intermediate.crt certs/ca.crt > intermediate/certs/ca-chain.cert.pem
```



# 5. Criar certificado do servidor Nginx (chave, CSR e assinatura pela Intermediária)

Exemplo usando `nginx.example.local` como CN e SAN (muito importante: browsers verificam SAN).

**Arquivo de extensões para servidor (`v3_server.cnf`)** — crie em `~/pki/server/v3_server.cnf`:

```ini
[ req ]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[ req_distinguished_name ]
C = BR
ST = Sao Paulo
L = Sao Paulo
O = MinhaEmpresa
OU = Servidores
CN = nginx.example.local

[ v3_req ]
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = nginx.example.local
DNS.2 = localhost
IP.1 = 127.0.0.1
```

**Gerar chave e CSR:**

```bash
cd ~/pki/server

openssl genpkey -algorithm RSA -out server.key -pkeyopt rsa_keygen_bits:2048
chmod 400 server.key

openssl req -new -key server.key -out server.csr -config v3_server.cnf
```

**Assinar CSR com a CA Intermediária (usando o openssl.cnf da intermediate):**

```bash
# usar o openssl ca da intermediate para emitir
cd ~/pki/intermediate

openssl ca -config openssl.cnf -extensions v3_intermediate_ca -days 825 \
  -notext -md sha256 \
  -in ../server/server.csr \
  -out ../server/server.crt \
  -batch \
  -keyfile private/intermediate.key -passin pass:senha_inter \
  -cert certs/intermediate.crt
```

> Atenção: ao usar `openssl ca` a configuração usada deve ter diretórios corretos; aqui usamos o `openssl.cnf` da `intermediate` (executado dentro de `~/pki/intermediate`), que aponta para os paths locais.

**Criar `fullchain` (server + intermediate) — usado pelo Nginx:**

```bash
cd ~/pki/server
cat server.crt ../intermediate/certs/intermediate.crt > fullchain.pem
```

Também copie (ou referencie) o certificado da raiz `~/pki/root/certs/ca.crt` para importação em navegadores.



# 6. Configurar Nginx para HTTPS

Exemplo de bloco de servidor (por ex. em `/etc/nginx/sites-available/nginx_example`):

```nginx
server {
    listen 443 ssl;
    server_name nginx.example.local;

    ssl_certificate     /etc/ssl/certs/nginx_example_fullchain.pem;   # fullchain.pem (server + intermediate)
    ssl_certificate_key /etc/ssl/private/nginx_example.key;

    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

**Instalar os arquivos gerados** (ajuste caminhos e permissões):

```bash
sudo mkdir -p /etc/ssl/private /etc/ssl/certs
sudo cp ~/pki/server/server.key /etc/ssl/private/nginx_example.key
sudo cp ~/pki/server/fullchain.pem /etc/ssl/certs/nginx_example_fullchain.pem
sudo chown root:root /etc/ssl/private/nginx_example.key /etc/ssl/certs/nginx_example_fullchain.pem
sudo chmod 400 /etc/ssl/private/nginx_example.key
sudo chmod 444 /etc/ssl/certs/nginx_example_fullchain.pem

# habilitar site e reiniciar nginx
sudo nginx -t && sudo systemctl reload nginx
```

Acesse `https://nginx.example.local/` no browser (lembre-se de que o nome DNS deve resolver para a máquina — edite `/etc/hosts` localmente se necessário):

```bash
echo "127.0.0.1 nginx.example.local" | sudo tee -a /etc/hosts
```



# 7. Importar CA Raiz no navegador (para confiar)

Pegue o arquivo `~/pki/root/certs/ca.crt` e importe no sistema/navegador:

**Firefox:** Preferências → Certificados → Autoridades → Importar → marcar confiança.

**Chrome/Edge:** importar no store do sistema.

Linux Debian/Ubuntu:

```bash
sudo cp ~/pki/root/certs/ca.crt /usr/local/share/ca-certificates/ca_minha_root.crt
sudo update-ca-certificates
```



# 8. Validar cadeia com OpenSSL

```bash
openssl verify -CAfile ~/pki/root/certs/ca.crt -untrusted ~/pki/intermediate/certs/intermediate.crt server.crt
```

```bash
openssl s_client -connect nginx.example.local:443 -servername nginx.example.local -CAfile ~/pki/root/certs/ca.crt
```

Resultado esperado:

```
Verify return code: 0 (ok)
```



