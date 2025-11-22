#!/usr/bin/env python3
"""
create_server_cert.py
Gera um certificado de servidor (ex: localhost) assinado pela CA Intermediária.
Saídas:
  - server.key   (chave privada)
  - server.csr   (pedido de assinatura)
  - server.crt   (certificado assinado)
  - chain.pem    (cadeia completa)
"""

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import datetime, os

# --- Caminhos ---
ROOT_DIR = "root"
INT_DIR = "intermediate"
SERVER_DIR = "server"
os.makedirs(SERVER_DIR, exist_ok=True)

INT_KEY_PATH = os.path.join(INT_DIR, "intermediate_ca.key")
INT_CERT_PATH = os.path.join(INT_DIR, "intermediate_ca.pem")

SERVER_KEY_PATH = os.path.join(SERVER_DIR, "server.key")
SERVER_CSR_PATH = os.path.join(SERVER_DIR, "server.csr")
SERVER_CERT_PATH = os.path.join(SERVER_DIR, "server.crt")
CHAIN_PATH = os.path.join(SERVER_DIR, "chain.pem")

# --- 1) Gerar chave privada do servidor ---
server_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,  # 2048 é suficiente para servidor; pode ser 4096
    backend=default_backend()
)

# --- 2) Criar CSR (para domínio localhost) ---
subject = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"BR"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"São Paulo"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, u"Sao Paulo"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Elder"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
])

# Subject Alternative Names (SAN) é essencial para browsers modernos
alt_names = [x509.DNSName(u"localhost"), x509.DNSName(u"127.0.0.1")]

csr = (
    x509.CertificateSigningRequestBuilder()
    .subject_name(subject)
    .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
    .sign(server_key, hashes.SHA256(), default_backend())
)

# --- 3) Carregar CA Intermediária ---
with open(INT_KEY_PATH, "rb") as f:
    int_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

with open(INT_CERT_PATH, "rb") as f:
    int_cert = x509.load_pem_x509_certificate(f.read(), backend=default_backend())

# --- 4) Assinar o CSR ---
now = datetime.datetime.utcnow()
valid_from = now - datetime.timedelta(days=1)
valid_to = now + datetime.timedelta(days=365 * 2)  # validade 2 anos

builder = (
    x509.CertificateBuilder()
    .subject_name(csr.subject)
    .issuer_name(int_cert.subject)
    .public_key(csr.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(valid_from)
    .not_valid_after(valid_to)
    # extensões
    .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
    .add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )
    .add_extension(
        x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
        critical=False,
    )
    .add_extension(
        x509.SubjectAlternativeName(alt_names),
        critical=False,
    )
    .add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_public_key(int_key.public_key()),
        critical=False,
    )
    .add_extension(
        x509.SubjectKeyIdentifier.from_public_key(csr.public_key()),
        critical=False,
    )
)

server_cert = builder.sign(private_key=int_key, algorithm=hashes.SHA256(), backend=default_backend())

# --- 5) Exportar arquivos ---
# chave privada
with open(SERVER_KEY_PATH, "wb") as f:
    f.write(
        server_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

# CSR
with open(SERVER_CSR_PATH, "wb") as f:
    f.write(csr.public_bytes(serialization.Encoding.PEM))

# certificado
with open(SERVER_CERT_PATH, "wb") as f:
    f.write(server_cert.public_bytes(serialization.Encoding.PEM))

# cadeia (server + intermediate + root)
with open(CHAIN_PATH, "wb") as f:
    with open(SERVER_CERT_PATH, "rb") as s, open(INT_CERT_PATH, "rb") as i, open(
        os.path.join(ROOT_DIR, "root_ca.pem"), "rb"
    ) as r:
        f.write(s.read())
        f.write(i.read())
        f.write(r.read())

print("Certificado de servidor criado:")
print(" - chave privada :", SERVER_KEY_PATH)
print(" - CSR           :", SERVER_CSR_PATH)
print(" - certificado   :", SERVER_CERT_PATH)
print(" - cadeia (chain):", CHAIN_PATH)
