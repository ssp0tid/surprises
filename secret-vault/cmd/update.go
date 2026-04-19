package cmd

import (
	"fmt"
	"os"

	"github.com/secret-vault/internal/vault"
	"github.com/spf13/cobra"
	"golang.org/x/term"
)

var updateCmd = &cobra.Command{
	Use:   "update <key>",
	Short: "Update a secret",
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

		fmt.Printf("Enter new secret value: ")
		value, err := term.ReadPassword(int(os.Stdin.Fd()))
		if err != nil {
			return err
		}
		fmt.Println()

		nonce, ciphertext, err := encrypt(string(value), password, v.KDFSalt)
		if err != nil {
			return err
		}

		if err := v.Update(key, nonce, ciphertext); err != nil {
			return err
		}

		if err := v.Save(path, password); err != nil {
			return err
		}

		fmt.Printf("Secret %s updated\n", key)
		return nil
	},
}