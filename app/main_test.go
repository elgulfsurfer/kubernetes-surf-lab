package main

import (
	"net/http"
	"testing"
)

func Test_main(t *testing.T) {
	tests := []struct {
		name string // description of this test case
	}{
		// TODO: Add test cases.
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			main()
		})
	}
}

func Test_fibonacci(t *testing.T) {
	tests := []struct {
		name string // description of this test case
		// Named input parameters for target function.
		n    int
		want []int
	}{
		// TODO: Add test cases.
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := fibonacci(tt.n)
			// TODO: update the condition below to compare got with tt.want.
			if true {
				t.Errorf("fibonacci() = %v, want %v", got, tt.want)
			}
		})
	}
}

func Test_loggingMiddleware(t *testing.T) {
	tests := []struct {
		name string // description of this test case
		// Named input parameters for target function.
		next http.Handler
		want http.Handler
	}{
		// TODO: Add test cases.
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := loggingMiddleware(tt.next)
			// TODO: update the condition below to compare got with tt.want.
			if true {
				t.Errorf("loggingMiddleware() = %v, want %v", got, tt.want)
			}
		})
	}
}
