.PHONY: fmt lint vet test test-race cover ci

GO ?= go

fmt:
	$(GO) fmt ./...

lint:
	golangci-lint run

vet:
	$(GO) vet ./...

test:
	$(GO) test ./...

test-race:
	$(GO) test -race ./...

cover:
	$(GO) test -coverprofile=coverage.out ./...
	$(GO) tool cover -func=coverage.out

ci: fmt vet test-race lint
