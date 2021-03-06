package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
)

type JobStatus struct {
	Name   string `json:"name"`
	Status string `json:"status"`
}

func JobsUpdate(_ context.Context, url string, name string, status string) error {
	data, err := json.Marshal(
		JobStatus{
			Name:   name,
			Status: status,
		},
	)
	if err != nil {
		return fmt.Errorf("not able to marshal json %v", err)
	}
	url = fmt.Sprintf("%s/api/jobs/hackernews/", url)
	req, err := http.NewRequest("PUT", url, bytes.NewBuffer(data))
	if err != nil {
		return fmt.Errorf("error getting response %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
	client := http.DefaultClient
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("error getting response %v", err)
	}
	resp.Body.Close()
	if resp.StatusCode >= 400 {
		return fmt.Errorf("error updating job %s with status %s", name, status)
	}
	return nil
}
