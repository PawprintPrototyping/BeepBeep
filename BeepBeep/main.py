from networking import WIFI

print("Connecting to wifi...")
WIFI.connect_wifi()
print(f"Connected? {WIFI.connected}")