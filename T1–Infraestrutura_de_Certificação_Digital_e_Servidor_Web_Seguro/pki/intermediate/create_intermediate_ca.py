#!/usr/bin/env python3
"""
create_intermediate_ca.py
Cria a CA Intermediária e assina o certificado com a Root CA existente.
Gera:
  - intermediate_ca.key   (chave privada)
  - intermediate_ca.csr   (pedido de assinatura)
  - intermediate_ca.pem   (certificado assinado pela Root)
"""

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import datetime, os

# --- Caminhos ---
ROOT_DIR = "root"
INT_DIR = "intermediate/"
os.makedirs(INT_DIR, exist_ok=True)

ROOT_KEY_PATH = os.path.join(ROOT_DIR, "root_ca.key")
ROOT_CERT_PATH = os.path.join(ROOT_DIR, "root_ca.pem")

INT_KEY_PATH = os.path.join(INT_DIR, "intermediate_ca.key")
INT_CSR_PATH = os.path.join(INT_DIR, "intermediate_ca.csr")
INT_CERT_PATH = os.path.join(INT_DIR, "intermediate_ca.pem")

# --- 1) Gerar chave privada da intermediária ---
int_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096,
    backend=default_backend()
)

# --- 2) Criar CSR ---
subject = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"BR"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"São Paulo"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, u"Sao Paulo"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Elder"),
    x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u"Intermediate CA"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"ElderIntermediateCA"),
])

csr = (
    x509.CertificateSigningRequestBuilder()
    .subject_name(subject)
    .sign(int_key, hashes.SHA256(), default_backend())
)

# --- 3) Carregar Root CA (chave e certificado) ---
with open(ROOT_KEY_PATH, "rb") as f:
    root_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

with open(ROOT_CERT_PATH, "rb") as f:
    root_cert = x509.load_pem_x509_certificate(f.read(), backend=default_backend())

# --- 4) Assinar o CSR com a Root CA ---
now = datetime.datetime.utcnow()
valid_from = now - datetime.timedelta(days=1)
valid_to = now + datetime.timedelta(days=365 * 2)  # validade de 2 anos

builder = (
    x509.CertificateBuilder()
    .subject_name(csr.subject)
    .issuer_name(root_cert.subject)
    .public_key(csr.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(valid_from)
    .not_valid_after(valid_to)
    # Extensões obrigatórias
    .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
    .add_extension(
        x509.KeyUsage(
            digital_signature=False,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=True,
            encipher_only=False,
            decipher_only=False
        ),
        critical=True,
    )
    .add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_public_key(root_key.public_key()),
        critical=False,
    )
    .add_extension(
        x509.SubjectKeyIdentifier.from_public_key(csr.public_key()),
        critical=False,
    )
)

intermediate_cert = builder.sign(private_key=root_key, algorithm=hashes.SHA256(), backend=default_backend())

# --- 5) Salvar arquivos ---
# chave privada da intermediária
with open(INT_KEY_PATH, "wb") as f:
    f.write(
        int_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

# CSR (opcional, apenas para referência)
with open(INT_CSR_PATH, "wb") as f:
    f.write(csr.public_bytes(serialization.Encoding.PEM))

# certificado da intermediária assinado pela Root
with open(INT_CERT_PATH, "wb") as f:
    f.write(intermediate_cert.public_bytes(serialization.Encoding.PEM))

print("CA Intermediária criada:")
print(" - chave privada :", INT_KEY_PATH)
print(" - CSR           :", INT_CSR_PATH)
print(" - certificado   :", INT_CERT_PATH)
