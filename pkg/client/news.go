package client

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"log"
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

type ItemResponse struct {
	Count   uint   `json:"count"`
	Results []Item `json:"results"`
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
	out := make(TopNews, 0)
	items := make(map[uint64]bool)
	for _, item := range i {
		items[item.ID] = true
		if len(item.Comments) == 0 {
			out = append(out, item.ID)
		}
	}
	if len(out) == 10 {
		return out, nil
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
	for _, i := range topStories {
		if _, ok := items[i]; !ok {
			if len(out) < 10 {
				out = append(out, i)
			} else {
				break
			}
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
	resp, err := http.Get(fmt.Sprintf("%s?page=1", url))
	if err != nil {
		return nil, fmt.Errorf("error getting response %v", err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("error getting response %v", err)
	}
	var items ItemResponse
	if err := json.Unmarshal(body, &items); err != nil {
		return nil, fmt.Errorf("error marshaling data %v", err)
	}
	log.Printf("found %d news items\n", items.Count)
	return items.Results, nil
}

func NewsCreate(_ context.Context, url string, item *Item) error {
	data, e := json.Marshal(item)
	if e != nil {
		return fmt.Errorf("not able to marshal json %v", e)
	}
	buffer := bytes.NewBuffer(data)
	url = fmt.Sprintf("%s/api/news/", url)
	resp, err := http.Post(url, "application/json", buffer)
	if err != nil {
		return fmt.Errorf("creation error %v", e)
	}
	resp.Body.Close()
	log.Println(resp.StatusCode)
	if resp.StatusCode == http.StatusOK {
		return nil
	}
	return errors.New("create failed")
}
