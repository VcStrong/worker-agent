// 签到与积分服务入口。环境变量：ADDR、STORE=memory|postgres、DATABASE_URL、RULES_FILE、RATE_LIMIT_ENABLED。
package main

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"demoapp/server/internal/clock"
	"demoapp/server/internal/httpapi"
	"demoapp/server/internal/ratelimit"
	"demoapp/server/internal/rules"
	"demoapp/server/internal/service"
	"demoapp/server/internal/store"
	"demoapp/server/internal/store/memory"
)

func main() {
	log := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	if err := run(log); err != nil {
		log.Error("fatal", "err", err.Error())
		os.Exit(1)
	}
}

func env(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func openStore(ctx context.Context, kind, dsn string) (store.Store, func(), error) {
	switch kind {
	case "memory":
		return memory.New(), func() {}, nil
	case "postgres":
		return openPG(ctx, dsn) // main_pg.go（-tags pg）或 main_nopg.go
	default:
		return nil, nil, fmt.Errorf("unknown STORE %q (want memory|postgres)", kind)
	}
}

func run(log *slog.Logger) error {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	cfg := rules.Default()
	if f := os.Getenv("RULES_FILE"); f != "" {
		c, err := rules.Load(f)
		if err != nil {
			return err
		}
		cfg = c
	}

	st, closeStore, err := openStore(ctx, env("STORE", "memory"), os.Getenv("DATABASE_URL"))
	if err != nil {
		return err
	}
	defer closeStore()

	var limiter *ratelimit.Limiter
	if env("RATE_LIMIT_ENABLED", "true") != "false" {
		limiter = ratelimit.New(10, time.Minute, nil) // R10：10 次/分钟/用户
	}

	var ready func(context.Context) error
	if p, ok := st.(interface{ Ping(context.Context) error }); ok {
		ready = p.Ping
	}

	svc := service.New(st, clock.Real{}, cfg, log)
	handler := httpapi.New(httpapi.Config{Service: svc, Limiter: limiter, Logger: log, Ready: ready})

	srv := &http.Server{
		Addr:              env("ADDR", ":8080"),
		Handler:           handler,
		ReadHeaderTimeout: 5 * time.Second,
		WriteTimeout:      8 * time.Second,
	}
	errCh := make(chan error, 1)
	go func() { errCh <- srv.ListenAndServe() }()
	log.Info("listening", "addr", srv.Addr, "store", env("STORE", "memory"))

	select {
	case err := <-errCh:
		if errors.Is(err, http.ErrServerClosed) {
			return nil
		}
		return err
	case <-ctx.Done():
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		return srv.Shutdown(shutdownCtx)
	}
}
