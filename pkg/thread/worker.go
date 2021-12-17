package thread

import (
	"context"
	"log"
)

type Worker interface {
	Start(ctx context.Context) error
	Close() error
}

func Start(ctx context.Context, w Worker) {
	for {
		if err := w.Start(ctx); err != nil {
			log.Println(err)
		}
	}
}

func Close(w Worker) error {
	return w.Close()
}
