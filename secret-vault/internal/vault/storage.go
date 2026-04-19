package vault

import (
	"crypto/rand"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"

	"github.com/secret-vault/internal/crypto"
)

var (
	ErrVaultNotFound = errors.New("vault file not found")
	ErrInvalidVault  = errors.New("invalid vault file")
)

func Load(path, password string) (*Vault, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil, ErrVaultNotFound
		}
		return nil, err
	}

	var v Vault
	if err := json.Unmarshal(data, &v); err != nil {
		return nil, ErrInvalidVault
	}

	if v.Version != VaultVersion {
		return nil, fmt.Errorf("unsupported vault version: %s", v.Version)
	}

	salt, err := DecodeBase64(v.KDFSalt)
	if err != nil {
		return nil, errors.New("invalid salt encoding")
	}

	key, err := crypto.GenerateKey(password, salt)
	if err != nil {
		return nil, err
	}
	defer crypto.SecureZero(key)

	for i := range v.Secrets {
		nonce, err := DecodeBase64(v.Secrets[i].Nonce)
		if err != nil {
			return nil, fmt.Errorf("invalid nonce for %s", v.Secrets[i].Key)
		}

		ciphertext, err := DecodeBase64(v.Secrets[i].Ciphertext)
		if err != nil {
			return nil, fmt.Errorf("invalid ciphertext for %s", v.Secrets[i].Key)
		}

		plaintext, err := crypto.AES256GCMDecrypt(key, nonce, ciphertext)
		if err != nil {
			return nil, fmt.Errorf("failed to decrypt %s: %w", v.Secrets[i].Key, err)
		}

		v.Secrets[i].Ciphertext = string(plaintext)
		crypto.SecureZero(plaintext)
	}

	return &v, nil
}

func (v *Vault) Save(path, password string) error {
	salt := make([]byte, 32)
	if _, err := io.ReadFull(rand.Reader, salt); err != nil {
		return err
	}

	key, err := crypto.GenerateKey(password, salt)
	if err != nil {
		return err
	}
	defer crypto.SecureZero(key)

	saveVault := *v
	saveVault.KDFSalt = EncodeBase64(salt)

	for i := range saveVault.Secrets {
		nonce, ciphertext, err := crypto.AES256GCMEncrypt(key, []byte(saveVault.Secrets[i].Ciphertext))
		if err != nil {
			return err
		}

		saveVault.Secrets[i].Nonce = EncodeBase64(nonce)
		saveVault.Secrets[i].Ciphertext = EncodeBase64(ciphertext)

		crypto.SecureZero(ciphertext)
	}

	data, err := json.MarshalIndent(saveVault, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(path, data, 0600)
}

func Init(path, password string) (*Vault, error) {
	v := New()

	salt := make([]byte, 32)
	if _, err := io.ReadFull(rand.Reader, salt); err != nil {
		return nil, err
	}
	v.KDFSalt = EncodeBase64(salt)

	if err := v.Save(path, password); err != nil {
		return nil, err
	}

	return v, nil
}