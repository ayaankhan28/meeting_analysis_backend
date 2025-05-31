from sqlalchemy import create_engine, Table, MetaData, Column, Integer, String, Text, ARRAY
from backend.app.config import DATABASE_URL

# Database setup
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define tables
videos = Table(
    "videos",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("video_url", String),
    Column("audio_url", String)
)

transcriptions = Table(
    "transcriptions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("video_id", Integer),
    Column("transcription", Text)
)

summaries = Table(
    "summaries",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("video_id", Integer),
    Column("summary", Text),
    Column("key_points", ARRAY(String))
)

metadata.create_all(engine)

def save_to_db(video_url, audio_url, transcription, summary, key_points):
    """Save results to the database."""
    try:
        with engine.begin() as conn:  # Use `begin()` to ensure commit
            result = conn.execute(
                videos.insert().returning(videos.c.id),
                {"video_url": video_url, "audio_url": audio_url}
            )
            video_id = result.scalar()  # Fetch the inserted video_id

            # Insert transcription and summary
            conn.execute(transcriptions.insert(), {"video_id": video_id, "transcription": transcription})
            conn.execute(summaries.insert(), {"video_id": video_id, "summary": summary, "key_points": key_points})

        print("Data saved to database successfully!")

    except Exception as e:
        print(f"Error inserting data into the database: {e}")

# Test
# save_to_db("test_url", "test_audio", "test_transcription", "test_summary", ["point1", "point2"])
