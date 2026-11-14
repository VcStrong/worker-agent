//go:build pg

package main

import (
	"context"
	"errors"

	"demoapp/server/internal/store"
	"demoapp/server/internal/store/postgres"
)

func openPG(ctx context.Context, dsn string) (store.Store, func(), error) {
	if dsn == "" {
		return nil, nil, errors.New("DATABASE_URL is required when STORE=postgres")
	}
	s, err := postgres.New(ctx, dsn)
	if err != nil {
		return nil, nil, err
	}
	return s, s.Close, nil
}
