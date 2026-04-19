package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"golang.org/x/term"
)

var (
	vaultPath string
	cfgFile string
)

func init() {
	cobra.OnInitialize(initConfig)

	rootCmd.PersistentFlags().StringVarP(&vaultPath, "vault", "v", "", "vault file path (default: ~/.secret-vault/vault)")
	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file path")

	rootCmd.AddCommand(initCmd)
	rootCmd.AddCommand(addCmd)
	rootCmd.AddCommand(getCmd)
	rootCmd.AddCommand(listCmd)
	rootCmd.AddCommand(deleteCmd)
	rootCmd.AddCommand(updateCmd)
	rootCmd.AddCommand(exportCmd)
	rootCmd.AddCommand(importCmd)
}

var rootCmd = &cobra.Command{
	Use:   "vault",
	Short: "Secret Vault - a secure secrets manager",
	Long:  `Secret Vault is a CLI tool for managing local secrets using AES-256-GCM encryption.`,
}

func initConfig() {
	if cfgFile != "" {
		viper.SetConfigFile(cfgFile)
	} else {
		home, err := os.UserHomeDir()
		if err == nil {
			viper.AddConfigPath(home + "/.secret-vault")
		}
		viper.SetConfigName("config")
	}
	viper.ReadInConfig()
}

func getVaultPath() (string, error) {
	if vaultPath != "" {
		return vaultPath, nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return home + "/.secret-vault/vault", nil
}

func promptPassword(prompt string) (string, error) {
	fmt.Print(prompt)
	password, err := term.ReadPassword(int(os.Stdin.Fd()))
	fmt.Println()
	return string(password), err
}

func Execute() error {
	return rootCmd.Execute()
}