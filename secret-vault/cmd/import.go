package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var importCmd = &cobra.Command{
	Use:   "import <file>",
	Short: "Import vault from encrypted file",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		srcPath := args[0]

		if _, err := os.Stat(srcPath); err != nil {
			return fmt.Errorf("file not found: %s", srcPath)
		}

		dstPath, err := getVaultPath()
		if err != nil {
			return err
		}

		if _, err := os.Stat(dstPath); err == nil {
			return fmt.Errorf("vault already exists at %s", dstPath)
		}

		password, err := promptPassword("Enter master password: ")
		if err != nil {
			return err
		}

		_, err = vault.Load(srcPath, password)
		if err != nil {
			return err
		}

		if err := copyFile(srcPath, dstPath); err != nil {
			return err
		}

		fmt.Printf("Vault imported from %s\n", srcPath)
		return nil
	},
}

func copyFile(src, dst string) error {
	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	return os.WriteFile(dst, data, 0600)
}