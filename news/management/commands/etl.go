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
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/spf13/cobra"
)

var url = fmt.Sprintf("%sscrutiny.local:%d/api/news/", "https://", 8081)

type TopNews []uint64

type News struct {
	PostedBY string    `db:"posted_by" json:"by"`
	Score    uint64    `db:"score" json:"score"`
	Slug     string    `db:"slug" json:"-"`
	StoryID  uint64    `db:"story_id" json:"id"`
	StoryURL string    `db:"story_url" json:"url"`
	Time     time.Time `db:"time" json:"-"`
	Title    string    `db:"title" json:"title"`
}

type jsonTime struct {
	time.Time
}

func (t *jsonTime) UnmarshalJSON(buf []byte) error {
	tt, err := time.Parse("2006-01-02T15:04:05", strings.Trim(string(buf), `"`))
	if err != nil {
		return err
	}
	t.Time = tt
	return nil
}

type NewsCreateRequest struct {
	PostedBY string   `json:"posted_by"`
	Score    uint64   `json:"score"`
	Slug     string   `json:"slug"`
	StoryID  uint64   `json:"story_id"`
	StoryURL string   `json:"story_url"`
	Time     jsonTime `json:"time"`
	Title    string   `json:"title"`
}

type req struct {
	Items []NewsCreateRequest `json:"items"`
}

type db struct {
	conn *sqlx.DB
}

func (c *db) connect() {
	db, err := sqlx.Connect("sqlite3", "db.sqlite3")
	if err != nil {
		log.Panic(err)
	}
	c.conn = db
}

func (c *db) close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

func (c *db) list(ctx context.Context) map[uint64]struct{} {
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
	var items []NewsCreateRequest
	if err := json.Unmarshal(body, &items); err != nil {
		log.Fatal("Error unmarshalling response. ", err)
	}
	out := make(map[uint64]struct{})
	for _, i := range items {
		out[i.StoryID] = struct{}{}
	}
	log.Printf("List took %s\n", time.Since(start))
	return out
}

func (c *db) create(_ context.Context, rows []NewsCreateRequest) error {
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

func Extract(ctx context.Context) <-chan *News {
	out := make(chan *News)
	go func() {
		defer close(out)
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
		for _, i := range topStories {
			wg.Add(1)
			go func(storyID uint64) {
				defer wg.Done()
				resp, err := http.Get(fmt.Sprintf("https://hacker-news.firebaseio.com/v0/item/%d.json", storyID))
				if err != nil {
					log.Fatal("Error getting response. ", err)
				}
				defer resp.Body.Close()
				body, err := ioutil.ReadAll(resp.Body)
				if err != nil {
					log.Fatal("Error reading response. ", err)
				}
				var news News
				if err := json.Unmarshal(body, &news); err != nil {
					log.Fatal("Error unmarshalling response. ", err)
				}
				select {
				case <-ctx.Done():
				case out <- &news:
				}
			}(i)
		}
		wg.Wait()
	}()
	return out
}

func Transform(ctx context.Context, stream <-chan *News) <-chan *News {
	out := make(chan *News)
	go func() {
		defer close(out)
		client := &db{}
		client.connect()
		defer client.close()
		items := client.list(ctx)
		for item := range stream {
			if _, ok := items[item.StoryID]; ok {
				continue
			}
			slug := uuid.New()
			item.Slug = slug.String()
			item.Time = time.Now().UTC()
			if item.StoryURL == "" {
				item.StoryURL = "https://test.com"
			}
			select {
			case <-ctx.Done():
			case out <- item:
			}
		}
	}()
	return out
}

func Load(ctx context.Context, stream <-chan *News) error {
	batchSize := 100
	client := &db{}
	client.connect()
	defer client.close()
	items := make([]NewsCreateRequest, 0)
	for item := range stream {
		items = append(items, NewsCreateRequest{
			PostedBY: item.PostedBY,
			Score:    item.Score,
			Slug:     item.Slug,
			StoryID:  item.StoryID,
			StoryURL: item.StoryURL,
			Title:    item.Title,
			Time:     jsonTime{Time: item.Time},
		})
		if len(items) >= batchSize {
			if err := client.create(ctx, items); err != nil {
				log.Println(err)
			}
			log.Printf("added %d stories\n", len(items))
			items = []NewsCreateRequest{}
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
