package main

import (
	"github.com/secret-vault/cmd"
)

func main() {
	if err := cmd.Execute(); err != nil {
		panic(err)
	}
}