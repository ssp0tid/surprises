package vault

import (
	"encoding/base64"
	"errors"
	"time"
)

const VaultVersion = "1.0"

type Secret struct {
	Key        string    `json:"key"`
	Nonce      string    `json:"nonce"`
	Ciphertext string   `json:"ciphertext"`
	Created    time.Time `json:"created"`
	Modified  time.Time `json:"modified"`
}

type Vault struct {
	Version  string    `json:"version"`
	Created  time.Time `json:"created"`
	Modified time.Time `json:"modified"`
	KDFSalt  string    `json:"kdf_salt"`
	Secrets []Secret  `json:"secrets"`
}

func New() *Vault {
	now := time.Now().UTC()
	return &Vault{
		Version:  VaultVersion,
		Created:  now,
		Modified: now,
		Secrets: []Secret{},
	}
}

func (v *Vault) Find(key string) (int, *Secret) {
	for i, s := range v.Secrets {
		if s.Key == key {
			return i, &s
		}
	}
	return -1, nil
}

func (v *Vault) Add(key, nonce, ciphertext string) {
	v.Modified = time.Now().UTC()
	v.Secrets = append(v.Secrets, Secret{
		Key:        key,
		Nonce:      nonce,
		Ciphertext: ciphertext,
		Created:    v.Modified,
		Modified:  v.Modified,
	})
}

func (v *Vault) Update(key, nonce, ciphertext string) error {
	v.Modified = time.Now().UTC()
	for i, s := range v.Secrets {
		if s.Key == key {
			v.Secrets[i].Nonce = nonce
			v.Secrets[i].Ciphertext = ciphertext
			v.Secrets[i].Modified = v.Modified
			return nil
		}
	}
	return errors.New("secret not found")
}

func (v *Vault) Delete(key string) error {
	v.Modified = time.Now().UTC()
	for i, s := range v.Secrets {
		if s.Key == key {
			v.Secrets = append(v.Secrets[:i], v.Secrets[i+1:]...)
			return nil
		}
	}
	return errors.New("secret not found")
}

func (v *Vault) Keys() []string {
	keys := make([]string, len(v.Secrets))
	for i, s := range v.Secrets {
		keys[i] = s.Key
	}
	return keys
}

func DecodeBase64(s string) ([]byte, error) {
	return base64.StdEncoding.DecodeString(s)
}

func EncodeBase64(b []byte) string {
	return base64.StdEncoding.EncodeToString(b)
}