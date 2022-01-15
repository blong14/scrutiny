package news

import (
	"context"
	"crypto/tls"
	"fmt"
	"log"
	"net/http"
	"strings"
	"sync"

	"github.com/google/uuid"
	"github.com/spf13/cobra"

	"scrutiny/pkg/client"
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
			//if len(item.Comments) > 0 {
			//	processChildren(ctx, out, i)
			//}
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
		log.Printf("found %d top stories\n", len(topStories))
		count := 1
		var wg sync.WaitGroup
		for _, i := range topStories {
			if count == 10 {
				break
			} else {
				count++
			}
			wg.Add(1)
			go func(storyID uint64) {
				defer wg.Done()
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
			}(i)
		}
		wg.Wait()
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
	batchSize := 100
	items := make([]client.Item, 0)
	for item := range stream {
		items = append(items, *item)
		if len(items) >= batchSize {
			if err := client.NewsCreate(ctx, fmt.Sprintf("%s/api/news/", url), items); err != nil {
				log.Println(err)
			}
			log.Printf("added %d stories\n", len(items))
			items = []client.Item{}
			if err := client.JobsUpdate(ctx, fmt.Sprintf("%s/api/jobs/hackernews/", url), client.JobStatus{Name: "hackernews", Status: "Healthy"}); err != nil {
				return err
			}
			log.Println("updated job status")
		}
	}
	if len(items) > 0 {
		if err := client.NewsCreate(ctx, fmt.Sprintf("%s/api/news/", url), items); err != nil {
			return err
		}
		log.Printf("added %d stories\n", len(items))
		if err := client.JobsUpdate(ctx, fmt.Sprintf("%s/api/jobs/hackernews/", url), client.JobStatus{Name: "hackernews", Status: "Healthy"}); err != nil {
			return err
		}
		log.Println("updated job status")
	}
	return nil
}

var NewsCmd = &cobra.Command{
	Use:   "news",
	Short: "Fetch news articles",
	Run: func(cmd *cobra.Command, _ []string) {
		http.DefaultTransport.(*http.Transport).TLSClientConfig = &tls.Config{InsecureSkipVerify: true}
		log.Println("starting news scrape...")
		ctx, cancel := context.WithCancel(context.Background())
		stream := Extract(ctx)
		stream = Transform(ctx, stream)
		if err := Load(ctx, stream); err != nil {
			log.Println(fmt.Errorf("load %v", err))
		}
		cancel()
		log.Println("finished news scrape")
	},
}
