package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var exportCmd = &cobra.Command{
	Use:   "export <file>",
	Short: "Export vault to encrypted file",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		srcPath, err := getVaultPath()
		if err != nil {
			return err
		}

		password, err := promptPassword("Enter master password: ")
		if err != nil {
			return err
		}

		v, err := vault.Load(srcPath, password)
		if err != nil {
			return err
		}

		dstPath := args[0]
		if err := v.Save(dstPath, password); err != nil {
			return err
		}

		fmt.Printf("Vault exported to %s\n", dstPath)
		return nil
	},
}