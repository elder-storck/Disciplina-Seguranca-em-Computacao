# Tarefa 2 — PKI (CA Raiz + Intermediária) e HTTPS com Nginx usando Scripts Python

* CA raiz (self-signed)
* CA intermediária (assinada pela raiz)
* Certificado de servidor (assinado pela intermediária)
* Configuração do Nginx usando esse certificado
* Importar a CA raiz no navegador para confiar no HTTPS
* Verificar a cadeia com `openssl verify` e `openssl s_client`

> Observação: Este ambiente utiliza **scripts Python** para automatizar a criação da infraestrutura de chave pública (PKI). Os caminhos abaixo foram adaptados exatamente conforme a estrutura do projeto exibida na imagem.

---

##  Estrutura do Projeto

```
CA-usando-Python/
└── pki/
    ├── root/
    │   ├── create_root_ca.py
    │   ├── root_ca.key
    │   └── root_ca.pem
    ├── intermediate/
    │   ├── create_intermediate_ca.py
    │   ├── intermediate_ca.key
    │   ├── intermediate_ca.csr
    │   └── intermediate_ca.pem
    └── server/
        ├── create_server_cert.py
        ├── server.key
        ├── server.csr
        ├── server.crt
        └── chain.pem
```

---

## 1. Criação da CA Raiz (Root CA)

A CA Raiz é o topo da hierarquia da PKI, sendo autoassinada e responsável por assinar a CA intermediária.

Entre no diretório:

```bash
cd CA-usando-Python/pki/root
```

Execute o script Python:

```bash
python3 create_root_ca.py
```

Este script é responsável por:

* Gerar a chave privada da Root CA (`root_ca.key`)
* Criar o certificado autoassinado (`root_ca.pem`)

Arquivos gerados:

*  `root_ca.key` – chave privada da CA raiz
*  `root_ca.pem` – certificado público da CA raiz

---

## 2. Criação da CA Intermediária

A CA intermediária é assinada pela raiz e é responsável por assinar certificados de servidores, evitando o uso direto da root em operações diárias.

Entre no diretório:

```bash
cd CA-usando-Python/pki/intermediate
```

Execute o script:

```bash
python3 create_intermediate_ca.py
```

Esse script realiza:

1. Geração da chave privada da intermediária
2. Criação do CSR (Certificate Signing Request)
3. Assinatura desse CSR pela CA raiz

Arquivos gerados:

*  `intermediate_ca.key` – chave privada da intermediária
*  `intermediate_ca.csr` – requisição de assinatura
*  `intermediate_ca.pem` – certificado final da intermediária (assinado pela root)

---

## 3. Criação do Certificado do Servidor

Agora criamos o certificado que será usado pelo Nginx, assinado pela CA intermediária.

Entre no diretório:

```bash
cd CA-usando-Python/pki/server
```

Execute o script:

```bash
python3 create_server_cert.py
```

O script:

* Gera a chave privada do servidor
* Cria o CSR com SAN (localhost, IP e domínio)
* Assina o CSR usando a CA intermediária
* Gera a cadeia completa

Arquivos resultantes:

*  `server.key` – chave privada do servidor
* `server.csr` – requisição de certificado
*  `server.crt` – certificado do servidor
*  `chain.pem` – cadeia completa (servidor + intermediária)

---

## 4. Configuração do Nginx para HTTPS

No arquivo de configuração do Nginx (ex: `default.conf` ou `nginx.conf`), utilizar:

```nginx
server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate     /etc/nginx/ssl/chain.pem;
    ssl_certificate_key /etc/nginx/ssl/server.key;

    root /usr/share/nginx/html;
    index index.html;
}
```

E mapear os volumes no Docker:

```yaml
volumes:
  - ./pki/server/chain.pem:/etc/nginx/ssl/chain.pem
  - ./pki/server/server.key:/etc/nginx/ssl/server.key
```

Reinicie o container após aplicar as alterações.

---

## 5. Importar CA Raiz no Navegador

Para evitar o erro de certificado inválido, importe o arquivo:

```
CA-usando-Python/pki/root/root_ca.pem
```

### Firefox

Configurações → Privacidade → Certificados → Autoridades → Importar → Confiar

### Linux (sistema):

```bash
sudo cp pki/root/root_ca.pem /usr/local/share/ca-certificates/minha_ca.crt
sudo update-ca-certificates
```

---

## 6. Validação da Cadeia SSL

### Verificar assinatura:

```bash
openssl verify -CAfile pki/root/root_ca.pem \
-untrusted pki/intermediate/intermediate_ca.pem \
pki/server/server.crt
```

### Testar conexão HTTPS:

```bash
openssl s_client -connect localhost:443 -servername localhost -CAfile pki/root/root_ca.pem
```

Resultado esperado:

```
Verify return code: 0 (ok)
```

---

## Resultado Final

Ao acessar: https://localhost

## Conclusão

A utilização de scripts Python automatiza todo o processo de criação da PKI, tornando-o mais reprodutível e menos sujeito a erro humano. A separação entre CA root e intermediária é uma prática recomendada que aumenta a segurança da infraestrutura, pois a raiz pode permanecer offline enquanto a intermediária é usada para emissões operacionais.

Essa abordagem simula de forma fiel o funcionamento de uma autoridade certificadora real, permitindo compreender na prática os conceitos fundamentais de criptografia, confiança e segurança em redes.
