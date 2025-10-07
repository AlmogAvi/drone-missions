import pandas as pd
import matplotlib.pyplot as plt
import sys

def main(csv_path: str):
    df = pd.read_csv(csv_path)
    if not {'lat','lon'}.issubset(df.columns):
        print("CSV must contain 'lat','lon'")
        return
    plt.figure()
    plt.plot(df['lon'], df['lat'], marker='.', linewidth=1)
    plt.title("Flight Track")
    plt.xlabel("Longitude"); plt.ylabel("Latitude")
    plt.axis('equal'); plt.grid(True)
    out = csv_path.replace(".csv", "_track.png")
    plt.savefig(out, dpi=160)
    print(f"Saved {out}")

if __name__ == "__main__":
    main(sys.argv[1])
