package news

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/google/brotli/go/cbrotli"
	"github.com/google/uuid"
	"github.com/spf13/cobra"
)

var url = fmt.Sprintf("%sscrutiny.local:%d/api/news/", "https://", 8081)
// var url = fmt.Sprintf("%sscrutiny.local:%d/api/news/", "http://", 8000)

type TopNews []uint64

type Item struct {
	Author    string    `json:"author"`
	CreatedAT time.Time `json:"created_at"`
	ID        uint64    `json:"id"`
	ParentID  *uint64   `json:"parent_id"`
	Points    uint64    `json:"points"`
	Slug      string    `json:"slug"`
	Title     string    `json:"title"`
	Text      string    `json:"text"`
	URL       string    `json:"url"`
}

type db struct{}

func (c *db) list(_ context.Context) map[uint64]struct{} {
	start := time.Now()
	resp, err := http.Get(url)
	if err != nil {
		log.Fatal("Error getting response. ", err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Fatal("Error reading response. ", err)
	}
	var items []Item
	if err := json.Unmarshal(body, &items); err != nil {
		log.Fatal("Error unmarshalling response. ", err)
	}
	out := make(map[uint64]struct{})
	for _, i := range items {
		out[i.ID] = struct{}{}
	}
	log.Printf("List took %s\n", time.Since(start))
	return out
}

func (c *db) create(_ context.Context, rows []Item) error {
	data, err := json.Marshal(rows)
	if err != nil {
		return fmt.Errorf("not able to marshal json %v", err)
	}
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(data))
	if err != nil {
		return fmt.Errorf("creation error %v", err)
	}
	log.Println(resp.Status, resp.StatusCode, resp.Header)
	resp.Body.Close()
	return nil
}

func Extract(ctx context.Context) <-chan *Item {
	out := make(chan *Item)
	go func() {
		defer close(out)
		client := &db{}
		items := client.list(ctx)
		resp, err := http.Get("https://hacker-news.firebaseio.com/v0/topstories.json")
		if err != nil {
			log.Fatal("Error getting response. ", err)
		}
		defer resp.Body.Close()
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			log.Fatal("Error reading response. ", err)
		}
		var topStories TopNews
		if err := json.Unmarshal(body, &topStories); err != nil {
			log.Fatal("Error unmarshalling response. ", err)
		}
		var wg sync.WaitGroup
		count := 1
		for _, i := range topStories {
			if _, ok := items[i]; ok {
				continue
			}
			if count == 10 {
				break
			} else {
				count++
			}
			wg.Add(1)
			go func(storyID uint64) {
				defer wg.Done()
				client := http.DefaultClient
				req, err := http.NewRequest(
					"GET", fmt.Sprintf("http://hn.algolia.com/api/v1/items/%d", storyID), nil)
				if err != nil {
					log.Fatal("Error getting response. ", err)
				}
				req.Header.Set("Accept", "*/*")
				req.Header.Set("Connection", "keep-alive")
				req.Header.Set("Accept-Encoding", "gzip, deflate, br")
				resp, err := client.Do(req)
				if err != nil {
					log.Fatal("Error getting response. ", err)
				}
				defer resp.Body.Close()
				var body []byte
				if resp.Header.Get("Content-Encoding") == "br" {
					reader := cbrotli.NewReader(resp.Body)
					defer reader.Close()
					body, err = ioutil.ReadAll(reader)
				} else {
					body, err = ioutil.ReadAll(resp.Body)
				}
				if err != nil {
					log.Fatal("Error reading response. ", err)
				}
				var item Item
				if err := json.Unmarshal(body, &item); err != nil {
					log.Fatal("Error unmarshalling response. ", err)
				}
				select {
				case <-ctx.Done():
				case out <- &item:
				}
			}(i)
		}
		wg.Wait()
	}()
	return out
}

func Transform(ctx context.Context, stream <-chan *Item) <-chan *Item {
	out := make(chan *Item)
	go func() {
		defer close(out)
		for item := range stream {
			slug := uuid.New()
			item.Slug = slug.String()
			if item.URL == "" {
				item.URL = "https://test.com"
			}
			select {
			case <-ctx.Done():
			case out <- item:
			}
		}
	}()
	return out
}

func Load(ctx context.Context, stream <-chan *Item) error {
	batchSize := 100
	client := &db{}
	items := make([]Item, 0)
	for item := range stream {
		items = append(items, *item)
		if len(items) >= batchSize {
			if err := client.create(ctx, items); err != nil {
				log.Println(err)
			}
			log.Printf("added %d stories\n", len(items))
			items = []Item{}
		}
	}
	if len(items) > 0 {
		if err := client.create(ctx, items); err != nil {
			return err
		}
		log.Printf("added %d stories\n", len(items))
	}
	return nil
}

var NewsCmd = &cobra.Command{
	Use:   "news",
	Short: "Fetch news articles",
	Run: func(cmd *cobra.Command, _ []string) {
		http.DefaultTransport.(*http.Transport).TLSClientConfig = &tls.Config{InsecureSkipVerify: true}
		ctx, cancel := context.WithCancel(context.Background())
		defer cancel()
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				log.Println("starting news scrape...")
				stream := Extract(ctx)
				stream = Transform(ctx, stream)
				if err := Load(ctx, stream); err != nil {
					log.Println(fmt.Errorf("load %v", err))
				}
			}
		}
	},
}
