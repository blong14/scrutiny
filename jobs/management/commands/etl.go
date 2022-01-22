package news

import (
	"context"
	"crypto/tls"
	"fmt"
	"github.com/google/uuid"
	"github.com/spf13/cobra"
	"log"
	"net/http"
	"strings"

	"scrutiny/pkg/client"
	"scrutiny/pkg/thread"
)

var url = fmt.Sprintf("http://scrutiny-caddy.default.svc.cluster.local:%d", 8443)

//var url = fmt.Sprintf("%sscrutiny.local:%d/api/news/", "http://", 8000)

func processChildren(ctx context.Context, out chan *client.Item, story client.Story) {
	for _, i := range story.Children {
		item := &client.Item{
			Author:    i.Author,
			CreatedAT: i.CreatedAT,
			ID:        i.ID,
			ParentID:  &story.ID,
			Points:    i.Points,
			Text:      i.Text,
			Title:     i.Title,
			Type:      i.Type,
			URL:       i.URL,
		}
		select {
		case <-ctx.Done():
			return
		case out <- item:
			if len(i.Children) > 0 {
				processChildren(ctx, out, i)
			}
		}
	}
}

func Extract(ctx context.Context) <-chan *client.Item {
	out := make(chan *client.Item)
	go func() {
		defer close(out)
		topStories, err := client.TopStories(ctx, fmt.Sprintf("%s/api/news/", url))
		if err != nil {
			log.Printf("extract error %s\n", err)
			return
		}
		for _, storyID := range topStories {
			story, err := client.GetStory(ctx, storyID)
			if err != nil {
				log.Printf("Error unmarshalling response. %s\n", err)
			}
			item := &client.Item{
				Author:    story.Author,
				CreatedAT: story.CreatedAT,
				ID:        story.ID,
				ParentID:  story.ParentID,
				Points:    story.Points,
				Text:      story.Text,
				Title:     story.Title,
				Type:      story.Type,
				URL:       story.URL,
			}
			select {
			case <-ctx.Done():
				return
			case out <- item:
			}
			if len(story.Children) > 0 {
				processChildren(ctx, out, story)
			}
		}
		log.Println("finished extracting top stories")
	}()
	return out
}

func Transform(ctx context.Context, stream <-chan *client.Item) <-chan *client.Item {
	out := make(chan *client.Item)
	go func() {
		defer close(out)
		log.Println("starting transformation stream")
		for i := range stream {
			slug := uuid.New()
			item := client.Item{
				Author:    i.Author,
				ID:        i.ID,
				CreatedAT: i.CreatedAT,
				ParentID:  i.ParentID,
				Points:    i.Points,
				Slug:      slug.String(),
				Text:      i.Text,
				Title:     i.Title,
				Type:      strings.ToUpper(i.Type),
				URL:       i.URL,
				Comments:  []uint64{},
			}
			if item.URL == "" {
				item.URL = "https://news.ycombinator.com"
			}
			if item.Author == "" {
				item.Author = "unknown"
			}
			if item.Type == "COMMENT" {
				if item.Title == "" {
					item.Title = "comment"
				}
			}
			select {
			case <-ctx.Done():
			case out <- &item:
			}
		}
		log.Println("closing transformation stream")
	}()
	return out
}

func Load(ctx context.Context, stream <-chan *client.Item) error {
	for item := range stream {
		if err := client.NewsCreate(ctx, url, item); err != nil {
			log.Println(err)
		}
	}
	err := client.JobsUpdate(ctx, url, "hackernews", "Healthy")
	if err != nil {
		return err
	}
	log.Println("updated job status")
	return nil
}

// worker implements thread.Worker
type worker struct {
}

func (w *worker) Start(ctx context.Context) error {
	log.Println("starting news scrape...")
	stream := Extract(ctx)
	stream = Transform(ctx, stream)
	if err := Load(ctx, stream); err != nil {
		return err
	}
	return nil
}

func (w *worker) Close() error {
	log.Println("finished news scrape")
	return nil
}

var NewsCmd = &cobra.Command{
	Use:   "news",
	Short: "Fetch news articles",
	Run: func(cmd *cobra.Command, _ []string) {
		http.DefaultTransport.(*http.Transport).TLSClientConfig = &tls.Config{InsecureSkipVerify: true}
		ctx, cancel := context.WithCancel(context.Background())
		if err := thread.Run(ctx, &worker{}); err != nil {
			log.Println(err)
		}
		cancel()
	},
}
