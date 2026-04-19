package cmd

import (
	"fmt"
	"os"

	"github.com/secret-vault/internal/vault"
	"github.com/spf13/cobra"
	"golang.org/x/term"
)

var addCmd = &cobra.Command{
	Use:   "add <key>",
	Short: "Add a secret",
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
		if _, exists := v.Find(key); exists != nil {
			return fmt.Errorf("secret %s already exists", key)
		}

		fmt.Printf("Enter secret value: ")
		value, err := term.ReadPassword(int(os.Stdin.Fd()))
		if err != nil {
			return err
		}
		fmt.Println()

		nonce, ciphertext, err := encrypt(value, password, v.KDFSalt)
		if err != nil {
			return err
		}

		v.Add(key, nonce, ciphertext)

		if err := v.Save(path, password); err != nil {
			return err
		}

		fmt.Printf("Secret %s added\n", key)
		return nil
	},
}