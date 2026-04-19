package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

var deleteCmd = &cobra.Command{
	Use:   "delete <key>",
	Short: "Delete a secret",
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
		if err := v.Delete(key); err != nil {
			return fmt.Errorf("secret %s not found", key)
		}

		if err := v.Save(path, password); err != nil {
			return err
		}

		fmt.Printf("Secret %s deleted\n", key)
		return nil
	},
}