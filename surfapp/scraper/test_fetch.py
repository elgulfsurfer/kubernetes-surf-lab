import requests

url = "https://www.ndbc.noaa.gov/data/realtime2/46225.txt"
resp = requests.get(url, timeout=30)
lines = resp.text.splitlines()
data_lines = [l for l in lines if not l.startswith("#") and l.strip()]

print("Raw line:")
print(data_lines[0])

parts = data_lines[0].split()
print(f"\nwave_height    (idx  8): {parts[8]}")
print(f"wave_period    (idx  9): {parts[9]}")
print(f"wave_direction (idx 11): {parts[11]}")
print(f"water_temp     (idx 14): {parts[14]}")
