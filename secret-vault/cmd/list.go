package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List all secrets",
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

		keys := v.Keys()
		if len(keys) == 0 {
			fmt.Println("No secrets found")
			return nil
		}

		fmt.Println("Secrets:")
		for _, k := range keys {
			fmt.Printf("  %s\n", k)
		}

		return nil
	},
}