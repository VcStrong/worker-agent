//go:build !pg

package main

import (
	"context"
	"errors"

	"demoapp/server/internal/store"
)

func openPG(_ context.Context, _ string) (store.Store, func(), error) {
	return nil, nil, errors.New("this binary was built without -tags pg; rebuild with: go build -tags pg ./cmd/server")
}
