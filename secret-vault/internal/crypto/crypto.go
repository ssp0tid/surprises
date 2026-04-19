package crypto

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"errors"
	"io"
)

// AES256GCM encrypts plaintext using AES-256-GCM with a new random nonce.
// Returns the nonce and ciphertext (both include the GCM auth tag).
func AES256GCMEncrypt(key, plaintext []byte) (nonce, ciphertext []byte, err error) {
	if len(key) != 32 {
		return nil, nil, errors.New("key must be 32 bytes for AES-256")
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, nil, err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, nil, err
	}

	// 96-bit nonce (12 bytes) - recommended for GCM
	nonce = make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, nil, err
	}

	// Sealappend includes the auth tag in the ciphertext
	ciphertext = gcm.Seal(nil, nonce, plaintext, nil)
	return nonce, ciphertext, nil
}

// AES256GCMDecrypt decrypts ciphertext using AES-256-GCM.
// The ciphertext should include the GCM auth tag.
func AES256GCMDecrypt(key, nonce, ciphertext []byte) ([]byte, error) {
	if len(key) != 32 {
		return nil, errors.New("key must be 32 bytes for AES-256")
	}
	if len(nonce) != 12 {
		return nil, errors.New("nonce must be 12 bytes")
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	// Openappend verifies the auth tag
	plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return nil, errors.New("decryption failed: authentication tag mismatch")
	}

	return plaintext, nil
}