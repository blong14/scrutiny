package news

import (
	"context"
	"database/sql"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"reflect"
	"regexp"
	"strings"

	"github.com/apache/beam/sdks/v2/go/pkg/beam"
	_ "github.com/apache/beam/sdks/v2/go/pkg/beam/core/runtime/exec/optimized"
	"github.com/apache/beam/sdks/v2/go/pkg/beam/io/databaseio"
	_ "github.com/apache/beam/sdks/v2/go/pkg/beam/runners/direct"
	_ "github.com/lib/pq"

	sclient "scrutiny/pkg/client"
)

var out = make(chan sclient.MercureRequest)

type event struct {
	EventID   string                 `db:"event_id"`
	EventType string                 `db:"event_type"`
	EventData sclient.MercureRequest `db:"event_data"`
	CreatedAT sql.NullTime           `db:"created_at"`
}

func read(ctx context.Context, msg event) {
	select {
	case <-ctx.Done():
		return
	case out <- msg.EventData:
		log.Printf("%+v\n", msg)
	}
}

func write(ctx context.Context, client *http.Client) {
	for {
		select {
		case <-ctx.Done():
			return
		case req := <-out:
			if err := sclient.Publish(ctx, client, &req); err != nil {
				log.Println(err)
			}
		}
	}
}

type OnItemCreated struct {
	DSN    string
	Runner string
}

func (o *OnItemCreated) Start(ctx context.Context) error {
	beam.Init()
	pipeline, root := beam.NewPipelineWithRoot()
	root.Scope("scrape-news-events")
	beam.ParDo0(root, read, databaseio.Query(
		root,
		"postgres",
		o.DSN,
		"EXPERIMENTAL CHANGEFEED FOR app.news_event;",
		reflect.TypeOf(event{}),
	))
	// TODO(Ben): figure out an http sink with the beam go sdk
	go write(ctx, &http.Client{})
	if _, err := beam.Run(ctx, o.Runner, pipeline); err != nil {
		log.Fatal(err)
	}
	return nil
}

func (o *OnItemCreated) Close() error {
	close(out)
	return nil
}

type Row struct {
	After struct {
		CreatedAt string `json:"created_at"`
		EventData string `json:"event_data"`
	} `json:"after"`
}

func (o *OnItemCreated) Read(_ context.Context) error {
	header := true
	csvReader := csv.NewReader(os.Stdin)
	for {
		rec, err := csvReader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Fatal(err)
		}
		if header {
			header = false
			continue
		}
		singleSpacePattern := regexp.MustCompile(`\s+`)
		var line []string
		for _, l := range rec {
			line = append(line, strings.TrimSpace(
				singleSpacePattern.ReplaceAllString(
					strings.Replace(l, "\"", "'", -1), ""),
			))
		}
		fmt.Println(line)
		var data Row
		if err := json.Unmarshal([]byte(line[2]), &data); err != nil {
			log.Fatal(err)
		}
		fmt.Printf("%+v\n", data)
	}
	return nil
}
