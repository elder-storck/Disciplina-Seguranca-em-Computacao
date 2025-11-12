#!/usr/bin/env python3
"""
create_root_ca.py
Gera uma Root CA (RSA 4096) autoassinada e exporta:
 - root_ca.key  (PEM, chave privada)
 - root_ca.pem  (PEM, certificado)
"""

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, NoEncryption
from cryptography.hazmat.backends import default_backend
import datetime
import os

OUT_DIR = "root/"
os.makedirs(OUT_DIR, exist_ok=True)

# 1) Gerar chave privada RSA 4096
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096,
    backend=default_backend()
)

# 2) Subject / Issuer (igual para self-signed)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"BR"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"São Paulo"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, u"Sao Paulo"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Elder"),
    x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u"Root CA"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"ElderRootCA"),
])

# 3) Montar o builder do certificado
now = datetime.datetime.utcnow()
valid_from = now - datetime.timedelta(days=1)
valid_to = now + datetime.timedelta(days=365*2)  # 2 anos

builder = x509.CertificateBuilder()
builder = builder.subject_name(subject)
builder = builder.issuer_name(issuer)
builder = builder.public_key(private_key.public_key())
builder = builder.serial_number(x509.random_serial_number())
builder = builder.not_valid_before(valid_from)
builder = builder.not_valid_after(valid_to)

# 4) Extensões essenciais para uma Root CA
# BasicConstraints: CA = True
builder = builder.add_extension(
    x509.BasicConstraints(ca=True, path_length=1), critical=True # path_length=1 permite que a Root assine uma intermediária (útil para cadeia com 1 intermediária)
)

# Key Usage
builder = builder.add_extension(
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
    critical=True
)

# Subject Key Identifier
builder = builder.add_extension(
    x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
    critical=False
)

# Authority Key Identifier (for roots usually same as subject key id)
builder = builder.add_extension(
    x509.AuthorityKeyIdentifier.from_issuer_public_key(private_key.public_key()),
    critical=False
)

# Optional: CRL Distribution Points or AIA can be added if you plan CRL/OCSP

# 5) Assinar (self-signed)
certificate = builder.sign(
    private_key=private_key, algorithm=hashes.SHA256(), backend=default_backend()
)

# 6) Exportar arquivos
KEY_PATH = os.path.join(OUT_DIR, "root_ca.key")
CERT_PATH = os.path.join(OUT_DIR, "root_ca.pem")

# Escrever chave privada (sem senha aqui; se quiser proteger, troque NoEncryption() por BestAvailableEncryption(b"senha"))
with open(KEY_PATH, "wb") as f:
    f.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,  # ou PKCS8
            encryption_algorithm=NoEncryption()  # para senha: BestAvailableEncryption(b"minhasenha")
        )
    )

# Escrever certificado PEM
with open(CERT_PATH, "wb") as f:
    f.write(
        certificate.public_bytes(encoding=serialization.Encoding.PEM)
    )

# 7) Segurança mínima do arquivo (Unix)
try:
    os.chmod(KEY_PATH, 0o600)
except Exception:
    pass

print("Root CA criada:")
print(" - chave privada:", KEY_PATH)
print(" - certificado   :", CERT_PATH)
