# app/core/data_loader.py

import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "../../Data")

def load_vehicle_chunks() -> list[dict]:
    """
    Converts each vehicle row into a rich descriptive text chunk.
    Each chunk also carries metadata for filtering in /recommend.
    """
    df = pd.read_csv(os.path.join(DATA_DIR, "ford_vehicles_dataset.csv"))
    chunks = []

    for _, row in df.iterrows():
        text = (
            f"Model: {row['Vehicle Model']}. "
            f"Body Style: {row['Body Style']}. "
            f"Engine: {row['Engine Specs']}. "
            f"Transmission: {row['Transmission Type']}. "
            f"Fuel Type: {row['Fuel Type']}. "
            f"Seating Capacity: {row['Seating Capacity']} seats. "
            f"Drivetrain: {row['Drivetrain']}. "
            f"Mileage: {row['Mileage']} {row['Mileage Unit']}. "
            f"Price: INR {row['Price (INR Lakhs)']} Lakhs. "
            f"Safety Features: {row['Safety Features']}."
        )
        chunks.append({
            "text": text,
            "source": "vehicle_specs",
            "model": row["Vehicle Model"],
            "body_style": row["Body Style"],
            "fuel_type": row["Fuel Type"],
            "seating": int(row["Seating Capacity"]),
            "drivetrain": row["Drivetrain"],
            "price": float(row["Price (INR Lakhs)"]),
            "safety_features": row["Safety Features"],
            "engine": row["Engine Specs"],
            "mileage": row["Mileage"],
            "mileage_unit": row["Mileage Unit"],
        })

    return chunks


def load_service_chunks() -> list[dict]:
    """
    Converts each service row into a maintenance summary text chunk.
    """
    df = pd.read_csv(os.path.join(DATA_DIR, "ford_vehicles_service_data.csv"))
    chunks = []

    for _, row in df.iterrows():
        text = (
            f"Service schedule for {row['Vehicle Model']}: "
            f"Oil change interval: {row['Oil Change Interval']}. "
            f"Tire rotation: {row['Tire Rotation Schedule']}. "
            f"Brake inspection: {row['Brake Inspection Frequency']}. "
            f"Warranty: {row['Warranty Details']}."
        )
        chunks.append({
            "text": text,
            "source": "service_data",
            "model": row["Vehicle Model"],
        })

    return chunks


def load_manual_chunks() -> list[dict]:
    """
    Splits the owner manual into paragraph-level chunks.
    Each section becomes a standalone searchable unit.
    """
    manual_path = os.path.join(DATA_DIR, "ford_owner_manual.txt")
    with open(manual_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by double newline to get logical paragraphs
    raw_chunks = [c.strip() for c in content.split("\n\n") if len(c.strip()) > 60]

    chunks = []
    for chunk in raw_chunks:
        chunks.append({
            "text": chunk,
            "source": "owner_manual",
            "model": "ALL",
        })

    return chunks


def load_all_chunks() -> list[dict]:
    """Master loader — returns all chunks from all 3 sources."""
    all_chunks = []
    all_chunks.extend(load_vehicle_chunks())
    all_chunks.extend(load_service_chunks())
    all_chunks.extend(load_manual_chunks())
    return all_chunks