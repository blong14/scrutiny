package thread

import (
	"context"
	"fmt"
)

type Worker interface {
	Start(ctx context.Context) error
	Close() error
}

func Run(ctx context.Context, w Worker) error {
	var err error
	if e := w.Start(ctx); e != nil {
		err = e
	}
	if e := w.Close(); e != nil {
		if err != nil {
			err = fmt.Errorf("%w with %s", err, e.Error())
		} else {
			err = e
		}
	}
	return err
}
