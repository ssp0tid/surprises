package cmd

import (
	"fmt"
	"os"

	"github.com/secret-vault/internal/vault"
	"github.com/spf13/cobra"
)

var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Initialize a new vault",
	RunE: func(cmd *cobra.Command, args []string) error {
		path, err := getVaultPath()
		if err != nil {
			return err
		}

		if _, err := os.Stat(path); err == nil {
			return fmt.Errorf("vault already exists at %s", path)
		}

		password, err := promptPassword("Enter master password: ")
		if err != nil {
			return err
		}

		confirm, err := promptPassword("Confirm password: ")
		if err != nil {
			return err
		}

		if password != confirm {
			return fmt.Errorf("passwords do not match")
		}

		_, err = vault.Init(path, password)
		if err != nil {
			return err
		}

		fmt.Printf("Vault initialized at %s\n", path)
		return nil
	},
}