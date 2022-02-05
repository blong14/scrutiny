package client

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"strings"
)

var mercureURL = "http://scrutiny-caddy.default:8443/.well-known/mercure"

type MercureRequest struct {
	Target string   `json:"target"`
	Topic  []string `json:"topic"`
	Data   string   `json:"data"`
}

func (m *MercureRequest) Encode() string {
	data := url.Values{}
	data.Set("data", m.Data)
	data.Set("target", m.Target)
	for _, t := range m.Topic {
		data.Set("topic", t)
	}
	return data.Encode()
}

func Publish(_ context.Context, client *http.Client, req *MercureRequest) error {
	r, err := http.NewRequest(http.MethodPost, mercureURL, strings.NewReader(req.Encode()))
	if err != nil {
		return fmt.Errorf("publish error %v", err)
	}
	r.Header.Add("Authorization", "Bearer token")
	r.Header.Add("Content-Type", "application/x-www-form-urlencoded")
	resp, err := client.Do(r)
	if err != nil {
		return fmt.Errorf("publish error %v", err)
	}
	resp.Body.Close()
	if resp.StatusCode >= http.StatusOK && resp.StatusCode < http.StatusBadRequest {
		return nil
	}
	return errors.New("published failed")
}
