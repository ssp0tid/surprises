package crypto

import (
	"crypto/rand"
	"errors"
	"io"

	"golang.org/x/crypto/argon2"
)

// KDFParams defines Argon2id parameters for key derivation.
// OWASP 2023 recommended parameters for password hashing.
var KDFParams = &Params{
	Memory:      64 * 1024, // 64 MB
	Iterations: 3,
	Parallelism: 4,
	SaltLen:    32,
	KeyLen:     32,
}

// Params holds Argon2id configuration.
type Params struct {
	Memory      uint32
	Iterations uint32
	Parallelism uint8
	SaltLen    uint32
	KeyLen     uint32
}

// GenerateKey derives a 32-byte key from password using Argon2id.
// Uses random salt if not provided.
func GenerateKey(password string, salt []byte) ([]byte, error) {
	if len(salt) == 0 {
		salt = make([]byte, KDFParams.SaltLen)
		if _, err := io.ReadFull(rand.Reader, salt); err != nil {
			return nil, err
		}
	}

	key := argon2.IDKey([]byte(password), salt, KDFParams.Iterations, KDFParams.Memory, KDFParams.Parallelism, KDFParams.KeyLen)
	return key, nil
}

// DeriveKeyWithParams derives a key with custom parameters.
func DeriveKeyWithParams(password string, salt []byte, p *Params) ([]byte, error) {
	if len(salt) == 0 {
		salt = make([]byte, p.SaltLen)
		if _, err := io.ReadFull(rand.Reader, salt); err != nil {
			return nil, err
		}
	}

	if len(salt) < 16 {
		return nil, errors.New("salt must be at least 16 bytes")
	}

	key := argon2.IDKey([]byte(password), salt, p.Iterations, p.Memory, p.Parallelism, p.KeyLen)
	return key, nil
}