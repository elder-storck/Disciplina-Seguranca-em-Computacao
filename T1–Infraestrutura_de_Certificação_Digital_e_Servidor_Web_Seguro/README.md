# <center> Relatório do Trabalho T1 </center>

## <center> Segurança em Computação – 2025/2 </center>

## <center> Infraestrutura de Certificação Digital: Let's Encrypt e PKI Própria </center>

---

### Informações do Grupo

* **Disciplina:** Segurança em Computação 2025/2
* **Integrantes:**

  * Nome: Thiago Felippe Neitzke Lahass
  * Nome: Afonso Salvador de Magalhães
  * Nome: Elder Ribeiro Storck
* **link do vídeo:** [Segurança em Computação 2025/2](https://drive.google.com/drive/folders/1E47q-tf8nVyrPOSFFEeFOrJgo7eQ4s0b?usp=sharing)


---

## 1. Arquitetura do Ambiente

Neste trabalho foram implementados dois cenários semelhantes, com a diferença de que, no Cenário 1, foi utilizado Python e, no Cenário 2, foi utilizado o OpenSSL.

* **Cenário 1:** Uso de scripts Python para automação da configuração HTTPS e gerenciamento de certificados.
* **Cenário 2:** Uso direto do OpenSSL para criação e gerenciamento manual dos certificados.

---

## 2. Tarefa 2 – HTTPS com PKI Própria (Root + Intermediária)

### 2.1. Criação da CA Raiz

A CA Raiz é uma autoridade certificadora autoassinada, sendo o nível mais importante da hierarquia de confiança.

### 2.2. Criação da CA Intermediária

O uso de uma CA intermediária possibilita manter a CA Raiz offline, aumentando a segurança do ambiente e limitando a exposição da chave privada da CA principal.

### 2.3. Emissão do Certificado do Servidor

O primeiro passo foi a criação do arquivo `server/server.csr` para que, posteriormente, ele fosse assinado pela CA intermediária, gerando o certificado `server.crt`.

### 2.4. Importação da CA Raiz no Navegador

O certificado da CA Raiz foi adicionado como confiável no navegador. Entretanto, mesmo após esse procedimento, o site ainda exibia a mensagem de conexão não segura, por se tratar de uma CA privada e não reconhecida por autoridades públicas.

---

## 3. Conclusões

Este trabalho apresentou a criação de uma CA Raiz e de uma CA Intermediária, além da configuração de um servidor Nginx utilizando um certificado assinado pela CA intermediária. Isso possibilitou um melhor entendimento das diferenças entre CA pública e privada, bem como dos processos envolvidos na criação e gerenciamento de uma PKI.

---

## Checklist Final

| Item                                        | Status |
| ------------------------------------------- | ------ |
| Servidor Nginx funcional (Docker)           | ✅      |
| PKI própria criada (Root + Intermediária)   | ✅      |
| Importação da CA Raiz no navegador          | ✅      |
| Cadeia de certificação validada com sucesso | ✅      |
| Relatório completo e entregue               | ✅      |
| Apresentação prática (vídeo)                | ✅      |

---
