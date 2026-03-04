package main

import (
	"flag"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
)

var version = "dev"

func main() {
	port := flag.Int("port", 8000, "port to listen on")
	flag.Parse()

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, "Hello!")
	})

	http.HandleFunc("/host", func(w http.ResponseWriter, r *http.Request) {
		host, err := os.Hostname()
		if err != nil {
			host = "unknown"
		}
		fmt.Fprint(w, host)
	})

	http.HandleFunc("/ip", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, localIP())
	})

	http.HandleFunc("/version", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, version)
	})

	http.HandleFunc("/fibonacci/", func(w http.ResponseWriter, r *http.Request) {
		nStr := strings.TrimPrefix(r.URL.Path, "/fibonacci/")
		n, err := strconv.Atoi(nStr)
		if err != nil || n < 0 {
			http.Error(w, "N must be a non-negative integer", http.StatusBadRequest)
			return
		}
		if n >= 40 {
			http.Error(w, "N must be less than 40", http.StatusBadRequest)
			return
		}
		seq := fibonacci(n)
		fmt.Fprint(w, seq)
	})

	fmt.Printf("listening on :%d\n", *port)
	http.ListenAndServe(fmt.Sprintf(":%d", *port), loggingMiddleware(http.DefaultServeMux))
}

type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (r *statusRecorder) WriteHeader(code int) {
	r.status = code
	r.ResponseWriter.WriteHeader(code)
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
		next.ServeHTTP(rec, r)
		log.Printf("%s %s %d %s", r.Method, r.URL.Path, rec.status, time.Since(start))
	})
}

func fibonacci(n int) []int {
	seq := make([]int, n)
	for i := range seq {
		if i == 0 {
			seq[i] = 0
		} else if i == 1 {
			seq[i] = 1
		} else {
			seq[i] = seq[i-1] + seq[i-2]
		}
	}
	return seq
}

func localIP() string {
	conn, err := net.Dial("udp", "8.8.8.8:80")
	if err != nil {
		return "unknown"
	}
	defer conn.Close()
	return conn.LocalAddr().(*net.UDPAddr).IP.String()
}
