package news

import (
	"context"
	"fmt"
	"github.com/google/uuid"
	"log"
	"strings"

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
			if len(i.Children) > 0 {
				processChildren(ctx, out, i)
			}
		}
	}
}

func extract(ctx context.Context) <-chan *client.Item {
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

func transform(ctx context.Context, stream <-chan *client.Item) <-chan *client.Item {
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

func load(ctx context.Context, stream <-chan *client.Item) error {
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

// TopStoriesETL implements thread.Worker
type TopStoriesETL struct {
}

func (w *TopStoriesETL) Start(ctx context.Context) error {
	log.Println("starting news scrape...")
	stream := extract(ctx)
	stream = transform(ctx, stream)
	if err := load(ctx, stream); err != nil {
		return err
	}
	return nil
}

func (w *TopStoriesETL) Close() error {
	log.Println("finished news scrape")
	return nil
}

func (w *TopStoriesETL) Read(_ context.Context) error {
	return nil
}
