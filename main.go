package main

import (
	"flag"
	"log"

	_ "github.com/mattn/go-sqlite3"
	"github.com/spf13/cobra"

	cmd "scrutiny/jobs/management/commands"
)

var rootCmd = &cobra.Command{
	Use:   "scrutiny",
	Short: "CLI for the scrutiny project...",
}

func init() {
	rootCmd.AddCommand(cmd.NewsCmd)
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
