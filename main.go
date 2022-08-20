package main

import (
	"flag"
	"log"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "scrutiny",
	Short: "CLI for the scrutiny project...",
}

func init() {
	cobra.OnInitialize(func() {
		log.Println("executing cmd")
	})
}

func execute() {
	if err := rootCmd.Execute(); err != nil {
		log.Panic(err)
	}
}

func main() {
	flag.Parse()
	execute()
}
