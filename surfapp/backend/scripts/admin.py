#!/usr/bin/env python3
"""
SurfLog Admin CLI
Run via: kubectl exec -it deployment/backend -- python3 /app/scripts/admin.py
"""

import json
import urllib.request
import urllib.error
import os

BASE = "http://localhost:5000"
KEY  = os.environ.get("ADMIN_API_KEY", "surfski34")


def post(path, data=None):
    body = json.dumps(data or {}).encode()
    req  = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        headers={"X-Admin-Key": KEY, "Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req)
        raw  = resp.read().decode()
        return json.loads(raw) if raw.strip() else {"ok": True}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return {"ERROR": json.loads(raw)}
        except Exception:
            return {"ERROR": raw}


def get(path):
    req = urllib.request.Request(
        f"{BASE}{path}",
        headers={"X-Admin-Key": KEY},
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"ERROR": e.read().decode()}


def prompt(label, secret=False):
    if secret:
        import getpass
        return getpass.getpass(f"  {label}: ")
    return input(f"  {label}: ").strip()


def pp(data):
    print(json.dumps(data, indent=2))


# ── Actions ───────────────────────────────────────────────────────────────────

def list_users():
    print("\n── Users ──")
    pp(get("/admin/users"))


def create_user():
    print("\n── Create User ──")
    email    = prompt("Email")
    password = prompt("Password", secret=True)
    pp(post("/admin/users", {"email": email, "password": password}))


def list_buoys():
    print("\n── Buoys ──")
    pp(get("/admin/buoys"))


def create_buoy():
    print("\n── Create Buoy ──")
    station_id = prompt("NOAA Station ID (e.g. 46225)")
    name       = prompt("Buoy name")
    pp(post("/admin/buoys", {"station_id": station_id, "name": name}))


def list_spots():
    print("\n── Spots ──")
    pp(get("/admin/spots"))


def create_spot():
    print("\n── Create Spot ──")
    name = prompt("Spot name")
    pp(post("/admin/spots", {"name": name}))


def assign_buoy_to_spot():
    print("\n── Assign Buoy → Spot ──")
    print("  (run 'List spots' and 'List buoys' first to get IDs)")
    spot_id = prompt("Spot ID")
    buoy_id = prompt("Buoy ID")
    result  = post(f"/admin/spots/{spot_id}/buoys/{buoy_id}")
    print("  ✓ Assigned" if not result.get("ERROR") else f"  ✗ {result}")


def assign_spot_to_user():
    print("\n── Assign Spot → User ──")
    print("  (run 'List users' and 'List spots' first to get IDs)")
    user_id = prompt("User ID")
    spot_id = prompt("Spot ID")
    result  = post(f"/admin/users/{user_id}/spots/{spot_id}")
    print("  ✓ Assigned" if not result.get("ERROR") else f"  ✗ {result}")


def cleanup_logs():
    print("\n── Cleanup Deleted Logs ──")
    confirm = prompt("Type 'yes' to delete soft-deleted logs older than 20 days")
    if confirm.lower() == "yes":
        pp(post("/admin/logs/cleanup"))
    else:
        print("  Cancelled.")


def trigger_scrape():
    print("\n── Manual Buoy Scrape ──")
    print("  Run this from your local terminal:")
    print("  kubectl create job scraper-manual --from=cronjob/scraper")
    print("  kubectl logs -f job/scraper-manual")


# ── Menu ──────────────────────────────────────────────────────────────────────

MENU = [
    ("List users",           list_users),
    ("Create user",          create_user),
    ("List buoys",           list_buoys),
    ("Create buoy",          create_buoy),
    ("List spots",           list_spots),
    ("Create spot",          create_spot),
    ("Assign buoy → spot",   assign_buoy_to_spot),
    ("Assign spot → user",   assign_spot_to_user),
    ("Cleanup deleted logs", cleanup_logs),
    ("Trigger buoy scrape",  trigger_scrape),
]


def main():
    print("\n╔══════════════════════════╗")
    print("║   SurfLog Admin CLI      ║")
    print("╚══════════════════════════╝")

    while True:
        print()
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  {i}.  {label}")
        print("  0.  Exit")
        print()

        choice = input("Select option: ").strip()

        if choice == "0":
            print("Bye.")
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(MENU):
            MENU[int(choice) - 1][1]()
        else:
            print("  Invalid option.")


if __name__ == "__main__":
    main()
