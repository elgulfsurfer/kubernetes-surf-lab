package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"html/template"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// ── Data structures ───────────────────────────────────────────────────────────

type Education struct {
	School     string   `json:"school"`
	Degree     string   `json:"degree"`
	Year       int      `json:"year"`
	Coursework []string `json:"coursework"`
}

type Experience struct {
	Title    string   `json:"title"`
	Dates    string   `json:"dates"`
	Company  string   `json:"company"`
	Location string   `json:"location"`
	Type     string   `json:"type"`
	Bullets  []string `json:"bullets"`
}

type Project struct {
	Name    string   `json:"name"`
	Dates   string   `json:"dates"`
	Bullets []string `json:"bullets"`
}

type Resume struct {
	Name       string       `json:"name"`
	Location   string       `json:"location"`
	Phone      string       `json:"phone"`
	Email      string       `json:"email"`
	LinkedIn   string       `json:"linkedin"`
	Education  Education    `json:"education"`
	Skills     []string     `json:"skills"`
	Experience []Experience `json:"experience"`
	Projects   []Project    `json:"projects"`
}

type Submission struct {
	Name      string `json:"name"`
	Email     string `json:"email"`
	Message   string `json:"message"`
	Timestamp int64  `json:"timestamp"`
}

// ── Templates ─────────────────────────────────────────────────────────────────

const resumeHTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{.Name}}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Georgia, serif; color: #222; background: #fff; padding: 40px 20px; }
    .container { max-width: 860px; margin: 0 auto; }
    h1 { font-size: 2rem; margin-bottom: 6px; }
    .contact-bar { font-size: 0.9rem; color: #444; margin-bottom: 32px; }
    .contact-bar a { color: #0055cc; text-decoration: none; }
    .contact-bar span { margin: 0 8px; color: #999; }
    h2 { font-size: 1rem; text-transform: uppercase; letter-spacing: 0.09em;
         border-bottom: 1px solid #ccc; padding-bottom: 4px; margin: 28px 0 14px; color: #333; }
    .edu-school { font-weight: bold; }
    .coursework { font-size: 0.88rem; color: #555; margin-top: 5px; }
    .skills { font-size: 0.95rem; line-height: 1.7; }
    .job { margin-bottom: 22px; }
    .entry-header { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 4px; }
    .entry-title { font-weight: bold; }
    .entry-dates { font-size: 0.88rem; color: #555; white-space: nowrap; }
    .entry-sub { font-size: 0.9rem; color: #444; margin: 4px 0 8px; }
    ul { padding-left: 20px; }
    li { margin-bottom: 5px; font-size: 0.93rem; line-height: 1.55; }
    .project { margin-bottom: 22px; }
    form { margin-top: 12px; }
    .form-group { margin-bottom: 16px; }
    label { display: block; font-size: 0.9rem; font-weight: bold; margin-bottom: 4px; }
    input[type=text], input[type=email], textarea {
      width: 100%; padding: 8px 10px; font-size: 0.95rem;
      border: 1px solid #bbb; border-radius: 3px; font-family: inherit; color: #222;
    }
    textarea { height: 130px; resize: vertical; }
    button {
      padding: 9px 24px; background: #222; color: #fff;
      border: none; border-radius: 3px; font-size: 0.95rem; cursor: pointer;
    }
    button:hover { background: #444; }
  </style>
</head>
<body>
<div class="container">

  <h1>{{.Name}}</h1>
  <div class="contact-bar">
    {{.Location}}<span>·</span>{{.Phone}}<span>·</span><a href="mailto:{{.Email}}">{{.Email}}</a><span>·</span><a href="{{.LinkedIn}}" target="_blank">LinkedIn</a>
  </div>

  <h2>Education</h2>
  <div>
    <span class="edu-school">{{.Education.School}}</span> — {{.Education.Degree}}, {{.Education.Year}}
    <div class="coursework">Coursework: {{join .Education.Coursework ", "}}</div>
  </div>

  <h2>Skills</h2>
  <div class="skills">{{join .Skills ", "}}</div>

  <h2>Experience</h2>
  {{range .Experience}}
  <div class="job">
    <div class="entry-header">
      <span class="entry-title">{{.Title}}</span>
      <span class="entry-dates">{{.Dates}}</span>
    </div>
    <div class="entry-sub">{{.Company}} &middot; {{.Location}} &middot; {{.Type}}</div>
    <ul>{{range .Bullets}}<li>{{.}}</li>{{end}}</ul>
  </div>
  {{end}}

  <h2>Projects</h2>
  {{range .Projects}}
  <div class="project">
    <div class="entry-header">
      <span class="entry-title">{{.Name}}</span>
      <span class="entry-dates">{{.Dates}}</span>
    </div>
    <ul>{{range .Bullets}}<li>{{.}}</li>{{end}}</ul>
  </div>
  {{end}}

  <h2>Contact</h2>
  <form method="POST" action="/contact">
    <div class="form-group">
      <label for="name">Name</label>
      <input type="text" id="name" name="name" required>
    </div>
    <div class="form-group">
      <label for="email">Email</label>
      <input type="email" id="email" name="email" required>
    </div>
    <div class="form-group">
      <label for="message">Message</label>
      <textarea id="message" name="message" required></textarea>
    </div>
    <button type="submit">Submit</button>
  </form>

</div>
</body>
</html>`

const thankyouHTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Thank You</title>
  <style>
    body { font-family: Georgia, serif; color: #222; background: #fff;
           padding: 80px 20px; text-align: center; }
    h1 { font-size: 1.8rem; margin-bottom: 12px; }
    p { font-size: 0.95rem; color: #444; margin-bottom: 8px; }
    a { color: #0055cc; text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <h1>Thank you for reaching out!</h1>
  <p>Your message has been received.</p>
  <p style="margin-top: 28px;"><a href="/">← Back to resume</a></p>
</body>
</html>`

const contactsHTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Contact Submissions</title>
  <style>
    body { font-family: Georgia, serif; color: #222; background: #fff; padding: 40px 20px; }
    .container { max-width: 860px; margin: 0 auto; }
    h1 { font-size: 1.5rem; margin-bottom: 24px; }
    .submission { border: 1px solid #ddd; border-radius: 4px; padding: 16px; margin-bottom: 14px; }
    .submission p { margin-bottom: 6px; font-size: 0.93rem; }
    .label { font-weight: bold; }
    .ts { color: #888; font-size: 0.85rem; }
    a { color: #0055cc; text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
<div class="container">
  <h1>Contact Submissions ({{len .}})</h1>
  {{if .}}
    {{range .}}
    <div class="submission">
      <p><span class="label">Name:</span> {{.Name}}</p>
      <p><span class="label">Email:</span> {{.Email}}</p>
      <p><span class="label">Message:</span> {{.Message}}</p>
      <p class="ts">Received: {{.Timestamp | formatTime}}</p>
    </div>
    {{end}}
  {{else}}
    <p>No submissions yet.</p>
  {{end}}
  <p style="margin-top: 28px;"><a href="/">← Back to resume</a></p>
</div>
</body>
</html>`

// ── Main ──────────────────────────────────────────────────────────────────────

func main() {
	port       := flag.Int("port", 8080, "port to listen on")
	resumeFile := flag.String("resume", "resume.json", "path to resume JSON file")
	dataDir    := flag.String("data", "./data", "directory for contact form submissions")
	flag.Parse()

	// Load resume
	f, err := os.Open(*resumeFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error opening resume file: %v\n", err)
		os.Exit(1)
	}
	defer f.Close()

	var resume Resume
	if err := json.NewDecoder(f).Decode(&resume); err != nil {
		fmt.Fprintf(os.Stderr, "error parsing resume JSON: %v\n", err)
		os.Exit(1)
	}

	// Ensure data directory exists
	if err := os.MkdirAll(*dataDir, 0755); err != nil {
		fmt.Fprintf(os.Stderr, "error creating data directory: %v\n", err)
		os.Exit(1)
	}

	// Template functions
	funcs := template.FuncMap{
		"join": strings.Join,
		"formatTime": func(ts int64) string {
			return time.Unix(ts, 0).Format("2006-01-02 15:04:05 MST")
		},
	}

	resumeTmpl   := template.Must(template.New("resume").Funcs(funcs).Parse(resumeHTML))
	thankyouTmpl := template.Must(template.New("thankyou").Parse(thankyouHTML))
	contactsTmpl := template.Must(template.New("contacts").Funcs(funcs).Parse(contactsHTML))

	// ── Routes ────────────────────────────────────────────────────────────────

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		resumeTmpl.Execute(w, resume)
	})

	http.HandleFunc("/contact", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Redirect(w, r, "/", http.StatusSeeOther)
			return
		}
		r.ParseForm()
		sub := Submission{
			Name:      r.FormValue("name"),
			Email:     r.FormValue("email"),
			Message:   r.FormValue("message"),
			Timestamp: time.Now().Unix(),
		}
		data, _ := json.MarshalIndent(sub, "", "  ")
		filename := filepath.Join(*dataDir, fmt.Sprintf("%d.json", sub.Timestamp))
		os.WriteFile(filename, data, 0644)
		thankyouTmpl.Execute(w, nil)
	})

	http.HandleFunc("/contacts", func(w http.ResponseWriter, r *http.Request) {
		entries, _ := os.ReadDir(*dataDir)
		var subs []Submission
		for _, e := range entries {
			if !strings.HasSuffix(e.Name(), ".json") {
				continue
			}
			b, err := os.ReadFile(filepath.Join(*dataDir, e.Name()))
			if err != nil {
				continue
			}
			var s Submission
			if err := json.Unmarshal(b, &s); err != nil {
				continue
			}
			subs = append(subs, s)
		}
		contactsTmpl.Execute(w, subs)
	})

	fmt.Printf("listening on :%d\n", *port)
	http.ListenAndServe(fmt.Sprintf(":%d", *port), nil)
}
