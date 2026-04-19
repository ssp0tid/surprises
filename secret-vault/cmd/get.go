package cmd

import (
	"fmt"

	"github.com/secret-vault/internal/crypto"
	"github.com/secret-vault/internal/vault"
	"github.com/spf13/cobra"
)

var reveal bool

var getCmd = &cobra.Command{
	Use:   "get <key>",
	Short: "Get a secret",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		path, err := getVaultPath()
		if err != nil {
			return err
		}

		password, err := promptPassword("Enter master password: ")
		if err != nil {
			return err
		}

		v, err := vault.Load(path, password)
		if err != nil {
			return err
		}

		key := args[0]
		_, secret := v.Find(key)
		if secret == nil {
			return fmt.Errorf("secret %s not found", key)
		}

		value, err := decryptValue(v.KDFSalt, password, secret.Nonce, secret.Ciphertext)
		if err != nil {
			return err
		}

		if reveal {
			fmt.Printf("%s\n", value)
		} else {
			fmt.Println("***SECRET***")
		}

		return nil
	},
}

func init() {
	getCmd.Flags().BoolVarP(&reveal, "reveal", "f", false, "show secret value")
}

func decryptValue(b64Salt, password, b64Nonce, b64Ciphertext string) (string, error) {
	salt, err := vault.DecodeBase64(b64Salt)
	if err != nil {
		return "", err
	}

	key, err := crypto.GenerateKey(password, salt)
	if err != nil {
		return "", err
	}
	defer crypto.SecureZero(key)

	nonce, err := vault.DecodeBase64(b64Nonce)
	if err != nil {
		return "", err
	}

	ciphertext, err := vault.DecodeBase64(b64Ciphertext)
	if err != nil {
		return "", err
	}

	plaintext, err := crypto.AES256GCMDecrypt(key, nonce, ciphertext)
	if err != nil {
		return "", err
	}

	result := string(plaintext)
	crypto.SecureZero(plaintext)
	return result, nil
}