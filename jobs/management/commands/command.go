package commands

import (
	"context"
	"crypto/tls"
	"log"
	"net/http"

	"github.com/spf13/cobra"

	"scrutiny/jobs/pkg/news"
	"scrutiny/pkg/thread"
)

var NewsCmd = &cobra.Command{
	Use:   "news",
	Short: "Fetch news articles",
	Run: func(cmd *cobra.Command, _ []string) {
		http.DefaultTransport.(*http.Transport).TLSClientConfig = &tls.Config{InsecureSkipVerify: true}
		ctx, cancel := context.WithCancel(context.Background())
		if err := thread.Run(ctx, &news.TopStoriesETL{}); err != nil {
			log.Println(err)
		}
		cancel()
	},
}
