# Secret Vault

A secure CLI secrets manager using AES-256-GCM encryption with Argon2id key derivation.

## Features

- **AES-256-GCM** authenticated encryption
- **Argon2id** OWASP 2023 recommended KDF
- **Master password** protection
- **Single encrypted vault file**
- **Secure memory handling**

## Installation

```bash
git clone https://github.com/secret-vault/secret-vault
cd secret-vault
go build -o secret-vault .
```

## Usage

### Initialize a new vault

```bash
./secret-vault init
```

### Add a secret

```bash
./secret-vault add api_key_prod
```

### Get a secret

```bash
./secret-vault get api_key_prod          # masked output
./secret-vault get api_key_prod -f     # reveal secret
```

### List all secrets

```bash
./secret-vault list
```

### Delete a secret

```bash
./secret-vault delete api_key_prod
```

### Update a secret

```bash
./secret-vault update api_key_prod
```

### Export vault

```bash
./secret-vault export backup.vault
```

### Import vault

```bash
./secret-vault import backup.vault
```

## Options

- `-v, --vault path`    Custom vault path
- `-f, --reveal`       Show secret value (get command)
- `-c, --clipboard`     Copy to clipboard

## Security

- Each secret encrypted with unique nonce
- GCM auth tag prevents tampering
- Key derived from password via Argon2id (64MB memory, 3 iterations)
- Password never stored, only in memory during operation
- Secrets zeroed from memory after use

## Default Vault Location

`~/.secret-vault/vault`

## Building

```bash
make build    # build binary
make test    # run tests
make clean   # clean artifacts
```