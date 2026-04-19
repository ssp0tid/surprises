package cmd

import (
	"github.com/secret-vault/internal/crypto"
	"github.com/secret-vault/internal/vault"
)

func encrypt(value, password, b64Salt string) (string, string, error) {
	salt, err := vault.DecodeBase64(b64Salt)
	if err != nil {
		return "", "", err
	}

	key, err := crypto.GenerateKey(password, salt)
	if err != nil {
		return "", "", err
	}
	defer crypto.SecureZero(key)

	nonce, ciphertext, err := crypto.AES256GCMEncrypt(key, []byte(value))
	if err != nil {
		return "", "", err
	}

	return vault.EncodeBase64(nonce), vault.EncodeBase64(ciphertext), nil
}

func decrypt(key, nonce, ciphertext string) (string, error) {
	n, err := vault.DecodeBase64(nonce)
	if err != nil {
		return "", err
	}

	c, err := vault.DecodeBase64(ciphertext)
	if err != nil {
		return "", err
	}

	plaintext, err := crypto.AES256GCMDecrypt([]byte(key), n, c)
	if err != nil {
		return "", err
	}

	result := string(plaintext)
	crypto.SecureZero(plaintext)
	return result, nil
}