package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"time"

	"github.com/google/brotli/go/cbrotli"
)

type TopNews []uint64

type Story struct {
	Author    string    `json:"author"`
	CreatedAT time.Time `json:"created_at"`
	ID        uint64    `json:"id"`
	ParentID  *uint64   `json:"parent"`
	Points    uint64    `json:"points"`
	Text      string    `json:"text"`
	Title     string    `json:"title"`
	Type      string    `json:"type"`
	URL       string    `json:"url"`
	Children  []Story   `json:"children"`
}

type Item struct {
	Author    string    `json:"author"`
	CreatedAT time.Time `json:"created_at"`
	ID        uint64    `json:"id"`
	ParentID  *uint64   `json:"parent"`
	Points    uint64    `json:"points"`
	Slug      string    `json:"slug"`
	Text      string    `json:"text"`
	Title     string    `json:"title"`
	Type      string    `json:"type"`
	URL       string    `json:"url"`
	Comments  []uint64  `json:"children"`
}

func TopStories(ctx context.Context, url string) (TopNews, error) {
	i, err := NewsList(ctx, url)
	if err != nil {
		return nil, fmt.Errorf("error getting response %v", err)
	}
	items := make(map[uint64]bool)
	for _, item := range i {
		items[item.ID] = true
	}
	resp, err := http.Get("https://hacker-news.firebaseio.com/v0/topstories.json")
	if err != nil {
		return nil, fmt.Errorf("error getting response %v", err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("error getting response %v", err)
	}
	var topStories TopNews
	if err := json.Unmarshal(body, &topStories); err != nil {
		return nil, fmt.Errorf("marshaling data %v", err)
	}
	out := make(TopNews, 0)
	for _, i := range topStories {
		if _, ok := items[i]; !ok {
			out = append(out, i)
		}
	}
	return out, nil
}

func GetStory(_ context.Context, storyID uint64) (Story, error) {
	client := http.DefaultClient
	req, err := http.NewRequest(
		"GET", fmt.Sprintf("http://hn.algolia.com/api/v1/items/%d", storyID), nil)
	if err != nil {
		return Story{}, fmt.Errorf("error getting response %v", err)
	}
	req.Header.Set("Accept", "*/*")
	req.Header.Set("Connection", "keep-alive")
	req.Header.Set("Accept-Encoding", "gzip, deflate, br")
	resp, err := client.Do(req)
	if err != nil {
		return Story{}, fmt.Errorf("error getting response %v", err)
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
		return Story{}, fmt.Errorf("error getting response %v", err)
	}
	var story Story
	if err := json.Unmarshal(body, &story); err != nil {
		return Story{}, fmt.Errorf("error unmarshaling data %v", err)
	}
	return story, nil
}

func NewsList(_ context.Context, url string) ([]Item, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("error getting response %v", err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("error getting response %v", err)
	}
	var items []Item
	if err := json.Unmarshal(body, &items); err != nil {
		return nil, fmt.Errorf("error marshaling data %v", err)
	}
	return items, nil
}

func NewsCreate(_ context.Context, url string, rows []Item) error {
	data, err := json.Marshal(rows)
	if err != nil {
		return fmt.Errorf("not able to marshal json %v", err)
	}
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(data))
	if err != nil {
		return fmt.Errorf("creation error %v", err)
	}
	resp.Body.Close()
	return nil
}
